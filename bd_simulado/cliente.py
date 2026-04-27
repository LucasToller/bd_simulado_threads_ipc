import argparse
from multiprocessing import Pipe, Process, freeze_support
from pathlib import Path

from servidor import iniciar_servidor

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_BANCO = BASE_DIR / "banco.json"
ARQUIVO_LOG = BASE_DIR / "sistema.log"
QUANTIDADE_THREADS = 4


def limpar_arquivos() -> None:
    ARQUIVO_BANCO.write_text("{}\n", encoding="utf-8")
    ARQUIVO_LOG.write_text("", encoding="utf-8")


def montar_requisicao(operacao: str, dados: dict | None = None) -> dict:
    return {
        "operacao": operacao.upper().strip(),
        "dados": dados or {},
    }


def enviar_e_aguardar(conexao, operacao: str, dados: dict | None = None) -> dict:
    requisicao = montar_requisicao(operacao, dados)
    conexao.send(requisicao)
    return conexao.recv()

def enviar_lote_e_aguardar(conexao, comandos: list[str]) -> bool:
    requisicoes = []
    encerrar_solicitado = False

    for texto in comandos:
        texto = texto.strip()

        if not texto:
            continue

        operacao, dados = interpretar_comando(texto)

        if operacao == "ENCERRAR":
            encerrar_solicitado = True
            continue

        requisicao = montar_requisicao(operacao, dados)
        requisicoes.append((texto, requisicao))

    if not requisicoes:
        return encerrar_solicitado

    print("\nEnviando requisicoes em lote, sem aguardar resposta individual...\n")

    for texto, requisicao in requisicoes:
        print(f"> enviado: {texto}")
        conexao.send(requisicao)

    print(f"\nTotal de requisicoes enviadas: {len(requisicoes)}")
    print("Aguardando respostas das threads...\n")

    for _ in range(len(requisicoes)):
        resposta = conexao.recv()
        imprimir_resposta(resposta)

    return encerrar_solicitado


def interpretar_comando(texto: str) -> tuple[str, dict]:
    partes = texto.strip().split()
    if not partes:
        raise ValueError("Comando vazio.")

    comando = partes[0].lower().strip()

    if comando in {"insert", "inserir"}:
        if len(partes) < 3:
            raise ValueError("Uso: INSERT <id> <nome>")
        return "INSERT", {"id": int(partes[1]), "nome": " ".join(partes[2:]).strip()}

    if comando in {"select", "buscar"}:
        if len(partes) == 1 or (len(partes) == 2 and partes[1] == "*"):
            return "LISTAR", {}
        return "SELECT", {"id": int(partes[1])}

    if comando in {"listar", "list"}:
        return "LISTAR", {}

    if comando in {"update", "atualizar"}:
        if len(partes) < 3:
            raise ValueError("Uso: UPDATE <id> <novo_nome>")
        return "UPDATE", {"id": int(partes[1]), "nome": " ".join(partes[2:]).strip()}

    if comando in {"delete", "remover", "excluir"}:
        if len(partes) != 2:
            raise ValueError("Uso: DELETE <id>")
        return "DELETE", {"id": int(partes[1])}

    if comando in {"sair", "encerrar"}:
        return "ENCERRAR", {}

    raise ValueError(f"Comando nao suportado: {partes[0]}")


def imprimir_lista_registros(registros: list[dict], numero_thread: str, titulo: str) -> None:
    print(f"[{numero_thread}] {titulo}")
    if not registros:
        print("banco vazio")
        return

    for registro in registros:
        print(f"id={registro['id']} nome={registro['nome']}")


def imprimir_resposta(resposta: dict) -> None:
    operacao = str(resposta.get("operacao", "")).upper().strip()
    sucesso = bool(resposta.get("sucesso"))
    mensagem = str(resposta.get("mensagem", "")).strip()
    dados = resposta.get("dados")
    numero_thread = str(resposta.get("thread_responsavel") or "servidor")

    if operacao == "ENCERRAR":
        print(f"\n[{numero_thread}] {mensagem}")
        return

    if operacao == "INSERT":
        if sucesso and isinstance(dados, dict):
            print(f"[{numero_thread}] INSERT ok -> id={dados['id']}, nome={dados['nome']}")
        else:
            print(f"[{numero_thread}] INSERT falhou: {mensagem}")
        return

    if operacao in {"SELECT", "LISTAR"}:
        if sucesso:
            titulo = "SELECT *" if operacao == "LISTAR" else "SELECT"
            if isinstance(dados, dict):
                print(f"[{numero_thread}] SELECT -> id={dados['id']} nome={dados['nome']}")
            elif isinstance(dados, list):
                imprimir_lista_registros(dados, numero_thread, titulo)
            else:
                print(f"[{numero_thread}] {mensagem}")
        else:
            comando = "SELECT" if operacao == "SELECT" else "LISTAR"
            print(f"[{numero_thread}] {comando} falhou: {mensagem}")
        return

    if operacao == "UPDATE":
        if sucesso and isinstance(dados, dict):
            print(f"[{numero_thread}] UPDATE ok -> id={dados['id']}, nome={dados['nome']}")
        else:
            print(f"[{numero_thread}] UPDATE falhou: {mensagem}")
        return

    if operacao == "DELETE":
        if sucesso and isinstance(dados, dict):
            print(f"[{numero_thread}] DELETE ok -> id={dados['id']}")
        else:
            print(f"[{numero_thread}] DELETE falhou: {mensagem}")
        return

    prefixo = "ok" if sucesso else "falhou"
    print(f"[{numero_thread}] {operacao} {prefixo}: {mensagem}")


def executar_modo_demo(conexao) -> None:
    print("\nExecutando lote de demonstracao...\n", flush=True)

    comandos = [
        "INSERT 1 Ana",
        "INSERT 2 Carlos",
        "INSERT 3 Beatriz",
        "SELECT 2",
        "UPDATE 1 Ana Paula",
        "DELETE 3",
        "SELECT *",
    ]

    for texto in comandos:
        print(f"> {texto}")
        operacao, dados = interpretar_comando(texto)
        resposta = enviar_e_aguardar(conexao, operacao, dados)
        imprimir_resposta(resposta)
        print()

    resposta = enviar_e_aguardar(conexao, "ENCERRAR", {})
    imprimir_resposta(resposta)


def executar_modo_carga(conexao) -> None:
    print("\nExecutando teste de carga concorrente...\n")

    comandos = [
        "INSERT 1 Ana",
        "INSERT 2 Carlos",
        "INSERT 3 Beatriz",
        "INSERT 4 Lucas",
        "INSERT 5 Felipe",
        "INSERT 6 Julia",
        "INSERT 7 Marcos",
        "INSERT 8 Amanda",
        "INSERT 9 Pedro",
        "INSERT 10 Camila",
        "INSERT 11 Gustavo",
        "INSERT 12 Laura",
    ]

    enviar_lote_e_aguardar(conexao, comandos)

    print("\nConferencia final do banco:\n")
    resposta = enviar_e_aguardar(conexao, "LISTAR", {})
    imprimir_resposta(resposta)

    resposta = enviar_e_aguardar(conexao, "ENCERRAR", {})
    imprimir_resposta(resposta)


def executar_modo_interativo(conexao) -> None:
    print("\nAgora voce pode testar manualmente.")
    print("Exemplos:")
    print("INSERT *id* *nome*")
    print("SELECT *id*")
    print("UPDATE *id* *novo nome*")
    print("DELETE *id*")
    print("SELECT *")
    print("Tambem pode enviar varios comandos na mesma linha usando ponto e virgula:")
    print("INSERT 1 Ana; INSERT 2 Carlos; INSERT 3 Lucas; SELECT *")
    print("Digite SAIR para encerrar.\n")

    while True:
        try:
            texto = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando cliente...")
            resposta = enviar_e_aguardar(conexao, "ENCERRAR", {})
            imprimir_resposta(resposta)
            break

        if not texto:
            continue

        try:
            if ";" in texto:
                comandos = [comando.strip() for comando in texto.split(";") if comando.strip()]
                encerrar_solicitado = enviar_lote_e_aguardar(conexao, comandos)

                if encerrar_solicitado:
                    resposta = enviar_e_aguardar(conexao, "ENCERRAR", {})
                    imprimir_resposta(resposta)
                    break

                continue

            operacao, dados = interpretar_comando(texto)
            resposta = enviar_e_aguardar(conexao, operacao, dados)
            imprimir_resposta(resposta)

            if operacao == "ENCERRAR":
                break

        except ValueError as erro:
            print(f"[cliente] {erro}")
        except Exception as erro:
            print(f"[cliente] Erro ao executar comando: {erro}")

def preparar_arquivos(resetar_dados: bool) -> None:
    if resetar_dados:
        limpar_arquivos()
        print("Dados e log resetados com sucesso.\n")
        return

    ARQUIVO_BANCO.touch(exist_ok=True)
    if ARQUIVO_BANCO.stat().st_size == 0:
        ARQUIVO_BANCO.write_text("{}\n", encoding="utf-8")
    ARQUIVO_LOG.touch(exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente do sistema de requisicoes paralelas.")
    parser.add_argument(
        "--modo",
        choices=["interativo", "demo", "carga"],
        default="interativo",
        help="Executa o cliente em modo interativo, demonstracao ou carga concorrente.",
    )
    parser.add_argument(
        "--resetar-dados",
        action="store_true",
        help="Limpa banco.json e sistema.log antes da execucao.",
    )
    args = parser.parse_args()

    preparar_arquivos(args.resetar_dados)

    conexao_cliente, conexao_servidor = Pipe(duplex=True)
    processo_servidor = Process(
        target=iniciar_servidor,
        args=(conexao_servidor, str(ARQUIVO_BANCO), str(ARQUIVO_LOG), QUANTIDADE_THREADS),
        name="processo_servidor",
        daemon=True,
    )
    processo_servidor.start()
    conexao_servidor.close()

    try:
        if args.modo == "demo":
            executar_modo_demo(conexao_cliente)
        elif args.modo == "carga":
            executar_modo_carga(conexao_cliente)
        else:
            executar_modo_interativo(conexao_cliente)
    finally:
        try:
            conexao_cliente.close()
        except Exception:
            pass

        processo_servidor.join(timeout=5)
        if processo_servidor.is_alive():
            processo_servidor.terminate()
            processo_servidor.join(timeout=2)


if __name__ == "__main__":
    freeze_support()
    main()