# Sistema de Processamento Paralelo de Requisicoes

## Visao geral
Projeto da disciplina de Sistemas Operacionais para simular o processamento paralelo de requisicoes a um banco de dados.

Nesta versao, o projeto foi deixado mais simples e proximo da estrutura sugerida no enunciado, mantendo:
- um processo cliente enviando requisicoes;
- um processo servidor recebendo as requisicoes via IPC com Pipe;
- pool de threads no servidor para processamento paralelo;
- banco simulado em arquivo JSON;
- controle de concorrencia com Lock;
- operacoes INSERT, SELECT, UPDATE, DELETE, LISTAR e ENCERRAR;
- registro das operacoes em arquivo de log.

Nesta etapa, o foco esta somente no terminal.

## Estrutura do projeto
```text
Sistema_de_Processamento_Paralelo_de_Requisicoes/
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

## Comandos disponiveis
- `INSERT <id> <nome>`
- `SELECT <id>`
- `SELECT *`
- `UPDATE <id> <novo_nome>`
- `DELETE <id>`
- `SAIR`

Tambem sao aceitos os equivalentes em portugues:
- `inserir`, `buscar`, `listar`, `atualizar`, `remover`, `encerrar`

## Fluxo do sistema
1. O cliente envia a requisicao via Pipe.
2. O servidor recebe a requisicao.
3. O servidor coloca a requisicao em uma fila interna.
4. As threads do pool processam as operacoes em paralelo.
5. O banco simulado usa Lock para evitar condicoes de corrida.
6. A resposta volta ao cliente e a execucao e registrada em `sistema.log`.

## Observacao
A estrutura foi simplificada para ficar mais proxima do modelo sugerido no PDF da atividade, sem frontend nesta entrega.
