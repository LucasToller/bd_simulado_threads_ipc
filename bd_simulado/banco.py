import json
import threading
from pathlib import Path


class BancoSimulado:
    def __init__(self, caminho_arquivo: str | Path) -> None:
        self.caminho_arquivo = Path(caminho_arquivo)
        self.lock = threading.Lock()
        self.dados: dict[str, dict] = {}
        self._carregar_banco()

    def _carregar_banco(self) -> None:
        if not self.caminho_arquivo.exists():
            self._salvar_banco()
            return

        conteudo = self.caminho_arquivo.read_text(encoding="utf-8").strip()
        if not conteudo:
            self._salvar_banco()
            return

        try:
            dados = json.loads(conteudo)
        except json.JSONDecodeError:
            self.dados = {}
            self._salvar_banco()
            return

        if isinstance(dados, list):
            self.dados = {}
            for item in dados:
                if isinstance(item, dict) and "id" in item and "nome" in item:
                    self.dados[str(int(item["id"]))] = {
                        "id": int(item["id"]),
                        "nome": str(item["nome"]),
                    }
            self._salvar_banco()
            return

        if isinstance(dados, dict):
            self.dados = {}
            for chave, valor in dados.items():
                if isinstance(valor, dict) and "id" in valor and "nome" in valor:
                    self.dados[str(chave)] = {
                        "id": int(valor["id"]),
                        "nome": str(valor["nome"]),
                    }
            return

        self.dados = {}
        self._salvar_banco()

    def _salvar_banco(self) -> None:
        self.caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_arquivo.write_text(
            json.dumps(self.dados, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    def inserir_registro(self, id_registro, nome):
        with self.lock:
            chave = str(int(id_registro))
            if chave in self.dados:
                return False, f"Ja existe um registro com id {id_registro}.", None

            registro = {"id": int(id_registro), "nome": str(nome).strip()}
            self.dados[chave] = registro
            self._salvar_banco()
            return True, f"Registro {id_registro} inserido com sucesso.", dict(registro)

    def buscar_registro(self, id_registro):
        with self.lock:
            chave = str(int(id_registro))
            registro = self.dados.get(chave)
            if registro is None:
                return False, f"Registro com id {id_registro} nao encontrado.", None
            return True, f"Registro {id_registro} encontrado.", dict(registro)

    def listar_registros(self):
        with self.lock:
            lista = sorted([dict(registro) for registro in self.dados.values()], key=lambda item: item["id"])
            return True, f"Total de registros: {len(lista)}.", lista

    def atualizar_registro(self, id_registro, nome):
        with self.lock:
            chave = str(int(id_registro))
            if chave not in self.dados:
                return False, f"Registro com id {id_registro} nao encontrado.", None

            nome_limpo = str(nome).strip()
            if not nome_limpo:
                return False, "O nome nao pode ficar vazio.", None

            self.dados[chave]["nome"] = nome_limpo
            self._salvar_banco()
            return True, f"Registro {id_registro} atualizado com sucesso.", dict(self.dados[chave])

    def remover_registro(self, id_registro):
        with self.lock:
            chave = str(int(id_registro))
            registro = self.dados.pop(chave, None)
            if registro is None:
                return False, f"Registro com id {id_registro} nao encontrado.", None

            self._salvar_banco()
            return True, f"Registro {id_registro} removido com sucesso.", dict(registro)