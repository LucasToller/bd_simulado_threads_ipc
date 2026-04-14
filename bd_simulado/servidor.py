import json
import logging
import queue
import threading
from datetime import datetime
from multiprocessing.connection import Connection
from pathlib import Path

from banco import BancoSimulado


TEMPO_ESPERA_PIPE = 0.2
TEMPO_ESPERA_FILA = 0.2


def agora_formatado() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def configurar_logger(caminho_log: Path) -> logging.Logger:
    logger = logging.getLogger("servidor_banco_simulado")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if logger.handlers:
        return logger

    formatador = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(threadName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    manipulador_arquivo = logging.FileHandler(caminho_log, encoding="utf-8")
    manipulador_arquivo.setFormatter(formatador)

    manipulador_console = logging.StreamHandler()
    manipulador_console.setFormatter(formatador)

    logger.addHandler(manipulador_arquivo)
    logger.addHandler(manipulador_console)
    return logger


def montar_resposta(operacao: str, sucesso: bool, mensagem: str, dados=None, thread_responsavel: str = "") -> dict:
    return {
        "operacao": operacao.upper().strip(),
        "sucesso": sucesso,
        "mensagem": mensagem,
        "dados": dados,
        "horario": agora_formatado(),
        "thread_responsavel": thread_responsavel,
    }


class ServidorBancoSimulado:
    def __init__(self, conexao: Connection, caminho_banco: str, caminho_log: str, quantidade_threads: int = 4) -> None:
        self.conexao = conexao
        self.caminho_banco = Path(caminho_banco)
        self.caminho_log = Path(caminho_log)
        self.caminho_banco.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_log.parent.mkdir(parents=True, exist_ok=True)
        self.logger = configurar_logger(self.caminho_log)
        self.banco = BancoSimulado(self.caminho_banco)
        self.quantidade_threads = quantidade_threads

        self.fila_requisicoes: queue.Queue[dict | None] = queue.Queue()
        self.fila_respostas: queue.Queue[dict | None] = queue.Queue()
        self.threads_trabalho: list[threading.Thread] = []
        self.thread_envio: threading.Thread | None = None
        self.lock_envio = threading.Lock()
        self.ativo = threading.Event()
        self.ativo.set()

    def iniciar(self) -> None:
        self.logger.info("Servidor iniciado com %s threads.", self.quantidade_threads)
        self._iniciar_threads()

        try:
            while self.ativo.is_set():
                if not self.conexao.poll(TEMPO_ESPERA_PIPE):
                    continue

                try:
                    requisicao = self.conexao.recv()
                except EOFError:
                    self.logger.info("Conexao com o cliente encerrada.")
                    break

                operacao = str(requisicao.get("operacao", "")).upper().strip()
                dados = requisicao.get("dados", {}) or {}
                self.logger.info("Requisicao recebida | operacao=%s | dados=%s", operacao, dados)

                if operacao == "ENCERRAR":
                    self._encerrar_com_resposta()
                    break

                self.fila_requisicoes.put(requisicao)
        finally:
            self._finalizar_servidor()

    def _iniciar_threads(self) -> None:
        for indice in range(self.quantidade_threads):
            thread = threading.Thread(
                target=self._executar_worker,
                name=f"worker-{indice + 1}",
                daemon=True,
            )
            thread.start()
            self.threads_trabalho.append(thread)

        self.thread_envio = threading.Thread(
            target=self._executar_envio_respostas,
            name="worker-envio",
            daemon=True,
        )
        self.thread_envio.start()

    def _executar_worker(self) -> None:
        while True:
            requisicao = self.fila_requisicoes.get()
            if requisicao is None:
                self.fila_requisicoes.task_done()
                break

            nome_thread = threading.current_thread().name
            resposta = self._processar_requisicao(requisicao, nome_thread)
            self.logger.info(
                "Requisicao processada | operacao=%s | sucesso=%s | thread=%s",
                resposta["operacao"],
                resposta["sucesso"],
                nome_thread,
            )
            self.fila_respostas.put(resposta)
            self.fila_requisicoes.task_done()

    def _executar_envio_respostas(self) -> None:
        while self.ativo.is_set() or not self.fila_respostas.empty():
            try:
                resposta = self.fila_respostas.get(timeout=TEMPO_ESPERA_FILA)
            except queue.Empty:
                continue

            if resposta is None:
                self.fila_respostas.task_done()
                break

            with self.lock_envio:
                self.conexao.send(resposta)
            self.fila_respostas.task_done()

    def _processar_requisicao(self, requisicao: dict, thread_responsavel: str) -> dict:
        operacao = str(requisicao.get("operacao", "")).upper().strip()
        dados = requisicao.get("dados", {}) or {}

        try:
            if operacao == "INSERT":
                sucesso, mensagem, retorno = self.banco.inserir_registro(dados["id"], dados["nome"])
                return montar_resposta(operacao, sucesso, mensagem, retorno, thread_responsavel)

            if operacao == "SELECT":
                if "id" not in dados:
                    sucesso, mensagem, retorno = self.banco.listar_registros()
                    return montar_resposta(operacao, sucesso, mensagem, retorno, thread_responsavel)
                sucesso, mensagem, retorno = self.banco.buscar_registro(dados["id"])
                return montar_resposta(operacao, sucesso, mensagem, retorno, thread_responsavel)

            if operacao == "LISTAR":
                sucesso, mensagem, retorno = self.banco.listar_registros()
                return montar_resposta(operacao, sucesso, mensagem, retorno, thread_responsavel)

            if operacao == "UPDATE":
                sucesso, mensagem, retorno = self.banco.atualizar_registro(dados["id"], dados["nome"])
                return montar_resposta(operacao, sucesso, mensagem, retorno, thread_responsavel)

            if operacao == "DELETE":
                sucesso, mensagem, retorno = self.banco.remover_registro(dados["id"])
                return montar_resposta(operacao, sucesso, mensagem, retorno, thread_responsavel)

            return montar_resposta(operacao, False, f"Operacao invalida: {operacao}.", None, thread_responsavel)
        except KeyError as erro:
            return montar_resposta(operacao, False, f"Campo obrigatorio ausente: {erro}", None, thread_responsavel)
        except ValueError as erro:
            return montar_resposta(operacao, False, f"Requisicao invalida: {erro}", None, thread_responsavel)
        except Exception as erro:
            return montar_resposta(operacao, False, f"Erro interno ao processar a requisicao: {erro}", None, thread_responsavel)

    def _encerrar_com_resposta(self) -> None:
        self.logger.info("Encerramento solicitado pelo cliente.")
        self.fila_requisicoes.join()
        self.fila_respostas.join()

        with self.lock_envio:
            self.conexao.send(
                montar_resposta(
                    operacao="ENCERRAR",
                    sucesso=True,
                    mensagem="Servidor encerrado com sucesso.",
                    dados=None,
                    thread_responsavel="servidor",
                )
            )
        self.ativo.clear()

    def _finalizar_servidor(self) -> None:
        self.ativo.clear()

        for _ in self.threads_trabalho:
            self.fila_requisicoes.put(None)

        for thread in self.threads_trabalho:
            thread.join(timeout=2)

        self.fila_respostas.put(None)
        if self.thread_envio is not None:
            self.thread_envio.join(timeout=2)

        try:
            self.conexao.close()
        except Exception:
            pass

        self.logger.info("Servidor finalizado.")


def iniciar_servidor(conexao: Connection, caminho_banco: str, caminho_log: str, quantidade_threads: int = 4) -> None:
    servidor = ServidorBancoSimulado(conexao, caminho_banco, caminho_log, quantidade_threads)
    servidor.iniciar()