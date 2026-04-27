# Sistema de Processamento Paralelo de Requisições

## Visão geral

Projeto da disciplina de Sistemas Operacionais para simular o processamento paralelo de requisições a um banco de dados.

O sistema possui:

- um processo cliente enviando requisições;
- um processo servidor recebendo requisições via IPC com `Pipe`;
- pool de threads no servidor para processar requisições de forma concorrente;
- banco simulado em arquivo JSON;
- controle de concorrência com `Lock`;
- operações `INSERT`, `SELECT`, `UPDATE`, `DELETE`, `LISTAR` e `ENCERRAR`;
- registro das operações em arquivo de log.

O projeto é executado pelo terminal.

## Estrutura do projeto

```text
bd_simulado_threads_ipc/
├── bd_simulado/
│   ├── cliente.py
│   ├── servidor.py
│   └── banco.py
├── requirements.txt
└── README.md
```

Durante a execução, o sistema gera automaticamente:

```text
bd_simulado/
├── banco.json
└── sistema.log
```

## Requisitos

- Python 3.10 ou superior
- Nenhuma biblioteca externa obrigatória

## Como executar

Abra o terminal dentro da pasta `bd_simulado`.

### Modo interativo

Permite digitar comandos manualmente:

```bash
python cliente.py --modo interativo
```

Com limpeza do banco e do log:

```bash
python cliente.py --modo interativo --resetar-dados
```

### Modo demonstração

Executa uma sequência fixa de comandos:

```bash
python cliente.py --modo demo
```

Com limpeza do banco e do log:

```bash
python cliente.py --modo demo --resetar-dados
```

### Modo carga concorrente

Envia várias requisições em lote para demonstrar o uso das threads do servidor:

```bash
python cliente.py --modo carga --resetar-dados
```

Esse é o modo recomendado para demonstrar a concorrência na apresentação.

## Comandos disponíveis

- `INSERT <id> <nome>`
- `SELECT <id>`
- `SELECT *`
- `UPDATE <id> <novo_nome>`
- `DELETE <id>`
- `LISTAR`
- `SAIR`

Também são aceitos equivalentes em português:

- `inserir`
- `buscar`
- `listar`
- `atualizar`
- `remover`
- `encerrar`

## Comandos em lote

No modo interativo, é possível enviar vários comandos na mesma linha usando ponto e vírgula:

```text
INSERT 1 Ana; INSERT 2 Carlos; INSERT 3 Lucas; INSERT 4 Julia
```

Depois, para conferir os registros:

```text
SELECT *
```

Para testes de concorrência, é recomendado usar comandos independentes no mesmo lote. Evite misturar operações dependentes, como `INSERT`, `UPDATE` e `DELETE` do mesmo ID na mesma linha, pois as threads podem processar as requisições em ordem diferente.

## Fluxo do sistema

1. O cliente envia uma requisição via `Pipe`.
2. O servidor recebe a requisição.
3. A requisição é colocada em uma fila interna.
4. As threads do servidor processam as requisições.
5. O banco JSON é acessado com proteção por `Lock`.
6. A resposta retorna ao cliente.
7. A operação é registrada em `sistema.log`.

## Conceitos utilizados

- IPC com `multiprocessing.Pipe`;
- criação de processo servidor com `multiprocessing.Process`;
- pool de threads com `threading.Thread`;
- fila de requisições com `queue.Queue`;
- controle de concorrência com `threading.Lock`;
- simulação de banco de dados em arquivo JSON.

## Teste recomendado

Para validar o funcionamento concorrente, execute:

```bash
python cliente.py --modo carga --resetar-dados
```

A saída deve mostrar diferentes threads processando requisições, como:

```text
[worker-1] INSERT ok
[worker-2] INSERT ok
[worker-3] INSERT ok
[worker-4] INSERT ok
```