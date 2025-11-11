# Ecommerce

## Descrição

Este projeto implementa um sistema de e-commerce com integração entre Python e MySQL, simulando o funcionamento básico de uma plataforma de vendas online.  
O sistema foi desenvolvido com foco em organização de dados relacionais, operações CRUD (Create, Read, Update, Delete) e interação via terminal.

##  Estrutura geral do projeto

| `Codigoecommerce.sql` | Contém a criação do banco de dados ecommerce, tabelas e inserções iniciais. 


| `codigopythonecommerce.py` | Código principal em Python com as operações de consulta, inserção, atualização e exclusão de dados. 


| `README.md` | Documento de explicação e instruções do projeto. 

## Estrutura do banco de dados utilizado

O banco de dados ecommerce contém tabelas principais que representam as entidades básicas de um comércio eletrônico.  
Entre elas são os clientes, produtos, pedidos, itens_pedido e categorias.
Essas tabelas possuem chaves primárias, estrangeiras e relacionamentos bem definidos, garantindo integridade referencial.

### Atributos de cada classe

#### Tabela **cliente**
| Atributo | Tipo | Descrição |


| `id` | INT (PK) | Identificador único do cliente |


| `nome` | VARCHAR(50) | Nome completo do cliente |


| `idade` | INT | Idade do cliente |


| `sexo` | CHAR(1) | Gênero: ‘m’, ‘f’ ou ‘o’ |


| `data_nascimento` | DATE | Data de nascimento |


#### Tabela **cliente_especial**
| Atributo | Tipo | Descrição |


| `id_cliente` | INT (PK, FK) | Referência ao cliente |


| `cashback` | DECIMAL(10,2) | Valor acumulado de cashback |

#### Tabela **vendedor**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador do vendedor |


| `nome` | VARCHAR(50) | Nome do vendedor |


| `causa_social` | VARCHAR(100) | Causa ou nome social |


| `tipo` | VARCHAR(50) | Categoria ou tipo de vendedor |


| `nota_media` | DECIMAL(3,2) | Avaliação média |


| `salario` | DECIMAL(10,2) | Salário atual |

#### Tabela **funcionario_especial**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador do funcionário |


| `id_vendedor` | INT (FK) | Referência ao vendedor |


| `bonus` | DECIMAL(10,2) | Valor do bônus atribuído |

#### Tabela **produto**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador do produto |


| `nome` | VARCHAR(50) | Nome do produto |


| `descricao` | TEXT | Descrição detalhada |


| `quantidade_estoque` | INT | Quantidade disponível |


| `valor` | DECIMAL(10,2) | Preço unitário |


| `observacoes` | TEXT | Observações adicionais |


| `id_vendedor` | INT (FK) | Vendedor responsável |


#### Tabela **transportadora**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador da transportadora |


| `nome` | VARCHAR(50) | Nome da empresa |


| `cidade` | VARCHAR(50) | Localização principal |


#### Tabela **transporte**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador do transporte |


| `id_transportadora` | INT (FK) | Transportadora responsável |


| `id_venda` | INT (FK) | Venda associada |


| `valor` | DECIMAL(10,2) | Valor do frete |



#### Tabela **venda**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador da venda |


| `data_venda` | DATE | Data da venda |


| `hora_venda` | TIME | Horário da venda |


| `valor` | DECIMAL(10,2) | Valor total da venda |


| `endereco` | VARCHAR(100) | Endereço de entrega |


| `id_cliente` | INT (FK) | Cliente comprador |


| `id_transporte` | INT (FK) | Transporte vinculado |


#### Tabela **venda_produto**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador |


| `id_venda` | INT (FK) | Venda associada |


| `id_produto` | INT (FK) | Produto vendido |


| `qtd` | INT | Quantidade |


| `valor` | DECIMAL(10,2) | Valor total (produto × qtd) |


| `obs` | VARCHAR(100) | Observações da venda |

#### Tabela **log_bonus**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador |


| `mensagem` | VARCHAR(255) | Mensagem de log |


| `criado_em` | TIMESTAMP | Data e hora de criação |


#### Tabela **log_cashback**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador |


| `mensagem` | VARCHAR(255) | Mensagem de log |


| `criado_em` | TIMESTAMP | Data e hora de criação |



#### Tabela **voucher**
| Atributo | Tipo | Descrição |

| `id` | INT (PK) | Identificador |


| `id_cliente` | INT (FK) | Cliente sorteado |


| `valor` | DECIMAL(10,2) | Valor do voucher |


| `criado_em` | TIMESTAMP | Data/hora da criação |

## Tecnologias Utilizadas

 **MySQL** —> Sistema de Gerenciamento de Banco de Dados Relacional  
**Python 3.x** —> Linguagem de programação usada para interação com o banco  
 **Biblioteca:** `mysql.connector` (nativa do pacote `mysql-connector-python`)  
 **Ambiente de desenvolvimento:** XAMPP / LAMPP (para o servidor local)

