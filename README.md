# Sistema de Requisicoes Paralelas

## Visao geral
Projeto da disciplina de Sistemas Operacionais para simular o processamento paralelo de requisicoes a um banco de dados.

**Projeto mantém o foco em:**
- comunicacao entre processos com **IPC via Pipe**;
- **processo cliente** enviando requisicoes;
- **processo servidor** recebendo e distribuindo tarefas;
- **pool de threads** no servidor;
- controle de concorrencia com **Lock** no banco simulado;
- operacoes **INSERT, SELECT, UPDATE, DELETE e LISTAR**;
- persistencia dos dados em arquivo **JSON** e registro das operacoes em **log**.


## Estrutura do projeto
```text
Sistema_de_Requisicoes_Paralelas_refatorado/
├── bd_simulado/
│   ├── cliente.py
│   ├── servidor.py
│   ├── banco.py
│   ├── banco.json
│   └── sistema.log
├── requirements.txt
└── README.md
```

## Requisitos
- Python 3.10 ou superior
- Nenhuma biblioteca externa obrigatoria

## Como executar
Abra o terminal dentro da pasta `bd_simulado`.

### Modo interativo
```bash
python cliente.py --modo interativo
```

### Modo demonstracao
```bash
python cliente.py --modo demo
```

### Modo demonstracao com limpeza do banco e do log
Recomendado para apresentacao:
```bash
python cliente.py --modo demo --resetar-dados
```

## Comandos disponiveis no terminal
- `inserir <id> <nome>`
- `buscar <id>`
- `listar`
- `atualizar <id> <novo_nome>`
- `remover <id>`
- `sair`

## Fluxo do sistema
1. O cliente monta a requisicao e envia via **Pipe**.
2. O servidor recebe a requisicao.
3. O servidor coloca a requisicao em uma fila interna.
4. As threads do pool processam as operacoes em paralelo.
5. O banco simulado usa **Lock** para evitar condicoes de corrida.
6. A resposta volta ao cliente e a execucao e registrada em `sistema.log`.

## Arquivos principais
### `cliente.py`
Responsavel por iniciar o processo servidor, enviar requisicoes e exibir as respostas no terminal.

### `servidor.py`
Responsavel por receber as requisicoes via Pipe, organizar a fila interna e distribuir o processamento entre as threads.

### `banco.py`
Responsavel pelo banco simulado em JSON, com operacoes de insercao, busca, listagem, atualizacao e remocao de registros.