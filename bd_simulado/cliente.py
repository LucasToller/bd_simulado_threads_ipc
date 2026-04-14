import argparse
from multiprocessing import Pipe, Process, freeze_support
from pathlib import Path

from servidor import iniciar_servidor

BASE_DIR = Path(__file__).resolve().parent
ARQUIVO_BANCO = BASE_DIR / "banco.json"
ARQUIVO_LOG = BASE_DIR / "sistema.log"


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


def interpretar_comando(texto: str) -> tuple[str, dict]:
    partes = texto.strip().split()
    if not partes:
        raise ValueError("Comando vazio.")

    comando = partes[0].lower().strip()

    if comando in {"insert", "inserir"}:
        if len(partes) < 3:
            raise ValueError("Uso: inserir <id> <nome>")
        return "INSERT", {"id": int(partes[1]), "nome": " ".join(partes[2:])}

    if comando in {"select", "buscar"}:
        if len(partes) == 1:
            return "SELECT", {}
        return "SELECT", {"id": int(partes[1])}

    if comando in {"listar", "list"}:
        return "LISTAR", {}

    if comando in {"update", "atualizar"}:
        if len(partes) < 3:
            raise ValueError("Uso: atualizar <id> <novo_nome>")
        return "UPDATE", {"id": int(partes[1]), "nome": " ".join(partes[2:])}

    if comando in {"delete", "remover", "excluir"}:
        if len(partes) < 2:
            raise ValueError("Uso: remover <id>")
        return "DELETE", {"id": int(partes[1])}

    if comando in {"sair", "encerrar"}:
        return "ENCERRAR", {}

    raise ValueError(f"Comando nao suportado: {comando}")


def imprimir_resposta(resposta: dict) -> None:
    status = "OK" if resposta.get("sucesso") else "ERRO"
    print(f"\n[{status}] {resposta.get('mensagem', '')}")
    print(f"Operacao: {resposta.get('operacao', 'N/A')}")
    print(f"Thread responsavel: {resposta.get('thread_responsavel', 'N/A')}")
    print(f"Horario: {resposta.get('horario', 'N/A')}")
    if resposta.get("dados") is not None:
        print(f"Dados: {resposta['dados']}")


def executar_modo_demo(conexao) -> None:
    print("\nExecutando lote de demonstracao...\n", flush=True)
    comandos = [
        ("INSERT", {"id": 1, "nome": "Lucas"}),
        ("INSERT", {"id": 2, "nome": "Maria"}),
        ("INSERT", {"id": 3, "nome": "Joao"}),
        ("SELECT", {"id": 1}),
        ("UPDATE", {"id": 2, "nome": "Maria Souza"}),
        ("SELECT", {"id": 2}),
        ("LISTAR", {}),
        ("DELETE", {"id": 1}),
        ("LISTAR", {}),
    ]

    for operacao, dados in comandos:
        resposta = enviar_e_aguardar(conexao, operacao, dados)
        imprimir_resposta(resposta)

    resposta = enviar_e_aguardar(conexao, "ENCERRAR", {})
    print(f"\nServidor: {resposta.get('mensagem', '')}")


def executar_modo_interativo(conexao) -> None:
    print("\nCliente iniciado. Comandos disponiveis:")
    print("- inserir <id> <nome>")
    print("- buscar <id>")
    print("- listar")
    print("- atualizar <id> <novo_nome>")
    print("- remover <id>")
    print("- sair")

    while True:
        try:
            texto = input("\nDigite um comando: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando cliente...")
            resposta = enviar_e_aguardar(conexao, "ENCERRAR", {})
            print(f"Servidor: {resposta.get('mensagem', '')}")
            break

        if not texto:
            continue

        try:
            operacao, dados = interpretar_comando(texto)
            resposta = enviar_e_aguardar(conexao, operacao, dados)
            imprimir_resposta(resposta)
            if operacao == "ENCERRAR":
                break
        except Exception as erro:
            print(f"\n[ERRO] {erro}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente do sistema de requisicoes paralelas.")
    parser.add_argument(
        "--modo",
        choices=["interativo", "demo"],
        default="interativo",
        help="Executa o cliente em modo interativo ou demonstracao.",
    )
    parser.add_argument(
        "--resetar-dados",
        action="store_true",
        help="Limpa banco.json e sistema.log antes da execucao.",
    )
    args = parser.parse_args()

    if args.resetar_dados:
        limpar_arquivos()
        print("Dados e log resetados com sucesso.\n")
    else:
        ARQUIVO_BANCO.touch(exist_ok=True)
        if ARQUIVO_BANCO.stat().st_size == 0:
            ARQUIVO_BANCO.write_text("{}\n", encoding="utf-8")
        ARQUIVO_LOG.touch(exist_ok=True)

    conexao_cliente, conexao_servidor = Pipe(duplex=True)

    processo_servidor = Process(
        target=iniciar_servidor,
        args=(conexao_servidor, str(ARQUIVO_BANCO), str(ARQUIVO_LOG), 4),
        name="processo_servidor",
        daemon=True,
    )
    processo_servidor.start()
    conexao_servidor.close()

    try:
        if args.modo == "demo":
            executar_modo_demo(conexao_cliente)
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