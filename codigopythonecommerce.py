import mysql.connector
from datetime import date, datetime
import random
import os
import time
from tabulate import tabulate
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- 1. Configuração do Banco de Dados e Conexão ---
DB_HOST = 'localhost'
DB_DATABASE = 'ecommerce'

# Variáveis GLOBAIS MUTÁVEIS para as credenciais atuais
CURRENT_USER = ''
CURRENT_PASSWORD = ''

def get_db_connection(use_db=True):
    """Cria e retorna uma conexão com o banco de dados (via XAMPP)."""
    if not CURRENT_USER or not CURRENT_PASSWORD:
        return None
        
    config = {
        'host': 'localhost',
        'user': CURRENT_USER,
        'password': CURRENT_PASSWORD,
        'unix_socket': '/opt/lampp/var/mysql/mysql.sock'  # <- ESSA LINHA É O SEGREDO!
    }
    
    if use_db:
        config['database'] = DB_DATABASE  # ex: ecommerce
    
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"[ERRO] Erro ao conectar ao MySQL: {err}")
        print("Verifique o usuário, senha e se o servidor está em execução.")
        return None


def execute_query(conn, query, params=None, fetch=False):
    """Executa consultas SQL e trata exceções."""
    try:
        # Usa dictionary=True para retornar resultados como dicionários (mais fácil de usar)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)

        results = []
        # Tenta buscar resultados (inclusive se for procedure)
        try:
            if fetch:
                while True:
                    part = cursor.fetchall()
                    if part:
                        results.extend(part)
                    # Tenta avançar se o método existir
                    if hasattr(cursor, "next_result"):
                        if not cursor.next_result():
                            break
                    else:
                        break
        except mysql.connector.InterfaceError:
            pass  # Nenhum outro conjunto de resultados
        except mysql.connector.ProgrammingError:
            pass

        conn.commit()
        cursor.close()
        return results if fetch else True

    except mysql.connector.Error as err:
        print(f"[ERRO] Erro de SQL: {err}")
        try:
            if conn.is_connected():
                conn.rollback()
        except:
            pass
        return None


def clear_screen():
    """Limpa o console."""
    os.system('cls' if os.name == 'nt' else 'clear')

# --- 2. Lógica de Permissões e Roles ---

def get_user_role():
    """Determina o papel do usuário com base no CURRENT_USER."""
    user = CURRENT_USER.lower()
    if user == 'admin':
        return 'Administrador'
    elif 'gerente' in user:
        return 'Gerente'
    elif 'funcionario' in user or 'vendedor' in user:
        return 'Funcionario'
    return 'Guest' 

def check_permission(required_roles):
    """Verifica se o usuário atual tem a permissão necessária."""
    current_role = get_user_role()
    if current_role == 'Administrador' or current_role in required_roles:
        return True
    print(f"\n[ERRO] ACESSO NEGADO. Seu papel ({current_role}) não tem permissão para esta ação.")
    return False

# --- 3. Dados Nativos e Setup ---

def preencher_dados_nativos(conn):
    """Insere dados de teste nas tabelas."""
    print("\nPreenchendo o banco de dados com dados nativos...")

    if not conn or not conn.is_connected():
        print("Não foi possível preencher dados: Conexão inválida.")
        return

    # Usamos execute_query para o restante das inserções, que gerencia o cursor.
    # O cursor é aberto e fechado dentro da execute_query
    
    # ========================
    # INSERIR FUNCIONÁRIOS
    # ========================
    funcionarios_data = []
    tipos_func = ["Vendedor", "Gerente", "CEO"]
    causas = ["Causa Ambiental", "Causa Social", "Causa Educacional", "Causa Animal", "Causa Tecnológica"]

    for i in range(1, 6):  # 5 funcionários
        nome = f"Funcionario {i}"
        tipo = random.choice(tipos_func)
        salario = {
            "Vendedor": round(random.uniform(1800, 3000), 2),
            "Gerente": round(random.uniform(4000, 7000), 2),
            "CEO": round(random.uniform(12000, 20000), 2)
        }[tipo]
        causa_social = random.choice(causas)
        nota_media = round(random.uniform(3.0, 5.0), 1)
        funcionarios_data.append((nome, salario, tipo, causa_social, nota_media))

    query_func = """
        INSERT INTO vendedor (nome, salario, tipo, causa_social, nota_media)
        VALUES (%s, %s, %s, %s, %s)
    """
    
    # O execute_query não tem executemany. Usamos cursor diretamente.
    cursor = conn.cursor()
    cursor.executemany(query_func, funcionarios_data)
    conn.commit()
    cursor.close()
    print("> 5 funcionários inseridos com sucesso.")

    # ========================
    # INSERIR CLIENTES
    # ========================
    clientes_data = []
    for i in range(1, 101):  # 100 clientes
        nome = f"Cliente {i}"
        idade = random.randint(18, 80)
        sexo = random.choice(['m', 'f', 'o'])
        ano_nasc = 2025 - idade
        data_nasc = date(year=ano_nasc, month=random.randint(1, 12), day=random.randint(1, 28))
        clientes_data.append((nome, idade, sexo, data_nasc))

    query_cliente = """
        INSERT INTO cliente (nome, idade, sexo, data_nascimento)
        VALUES (%s, %s, %s, %s)
    """
    cursor = conn.cursor()
    cursor.executemany(query_cliente, clientes_data)
    conn.commit()
    cursor.close()
    print("> 100 clientes inseridos com sucesso.")

    # ========================
    # INSERIR PRODUTOS
    # ========================
    # IDs válidos de funcionários (vendedores/gerentes/CEOs)
    vendedor_ids = list(range(1, 6))

    produtos_data = []
    for i in range(1, 21):  # 20 produtos
        nome = f"Produto {i}"
        descricao = f"Descrição do produto {i}"
        estoque = random.randint(50, 500)
        valor = round(random.uniform(30.0, 1000.0), 2)
        id_vendedor = random.choice(vendedor_ids)
        produtos_data.append((nome, descricao, estoque, valor, id_vendedor))

    query_produto = """
        INSERT INTO produto (nome, descricao, quantidade_estoque, valor, id_vendedor)
        VALUES (%s, %s, %s, %s, %s)
    """
    cursor = conn.cursor()
    cursor.executemany(query_produto, produtos_data)
    conn.commit()
    cursor.close()
    print("> 20 produtos inseridos com sucesso.")

    # ========================
    # INSERIR TRANSPORTADORAS
    # ========================
    query_transp = """
        INSERT INTO transportadora (nome, cidade)
        VALUES ('Rapidex', 'São Paulo'),
               ('Entrega Já', 'Rio de Janeiro'),
               ('LogMaster', 'Belo Horizonte'),
               ('ViaSul', 'Porto Alegre'),
               ('Correios Turbo', 'Recife')
    """
    cursor = conn.cursor()
    cursor.execute(query_transp)
    conn.commit()
    cursor.close()
    print("> 5 transportadoras inseridas com sucesso.")

    print("\n[SUCESSO] Dados nativos inseridos com sucesso!")

def criar_e_destruir_db():
    """ADMIN: Preenche o banco de dados com dados nativos, assumindo que o DDL já foi criado."""
    if not check_permission(['Administrador']):
        return

    print("\n--- ATENÇÃO: Esta opção tentará preencher dados nativos.")
    confirm = input("Deseja tentar preencher dados nativos no DB 'ecommerce' existente? (s/n): ").strip().lower()
    if confirm != 's':
        print("Ação cancelada pelo usuário.")
        return

    conn = get_db_connection()
    if not conn:
        print("[ERRO] Falha na conexão. Certifique-se de que o DB 'ecommerce' existe e está acessível.")
        return

    cursor = None
    try:
        cursor = conn.cursor()

        print("\n> Limpando tabelas antes do preenchimento...")
        comandos_limpeza = [
            "SET FOREIGN_KEY_CHECKS = 0",
            "TRUNCATE TABLE venda_produto",
            "TRUNCATE TABLE venda",
            "TRUNCATE TABLE cliente_especial",
            "TRUNCATE TABLE cliente",
            "TRUNCATE TABLE produto",
            "TRUNCATE TABLE vendedor",
            "TRUNCATE TABLE transportadora",
            "SET FOREIGN_KEY_CHECKS = 1"
        ]

        for cmd in comandos_limpeza:
            cursor.execute(cmd)

        conn.commit()
        print("> Tabelas limpas com sucesso.")

        print("\n> Iniciando preenchimento com dados nativos...")
        preencher_dados_nativos(conn)
        print("> Dados nativos inseridos com sucesso!")

    except TypeError as te:
        print(f"[ERRO DE TIPO] Verifique o uso de execute/executemany em 'preencher_dados_nativos': {te}")
    except Exception as e:
        print(f"[ERRO GERAL] Ocorreu um erro ao preencher os dados nativos: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            
    input("Pressione Enter para continuar...")

# --- 4. Funções CRUD (Adição) ---

def cadastrar_produto(conn):
    """ADMIN/FUNCIONARIO: Cadastra um novo produto."""
    if not check_permission(['Administrador', 'Funcionario']): return 
    print("\n--- Adicionar Novo Produto ---")
    
    nome = input("Nome do Produto: ")
    descricao = input("Descrição: ")
    try:
        estoque = int(input("Quantidade em Estoque: "))
        valor = float(input("Valor (ex: 12.50): "))
        id_vendedor = int(input("ID do Vendedor responsável: "))
    except ValueError:
        print("[ERRO] Entrada numérica inválida. Cadastro cancelado.")
        return
        
    observacoes = input("Observações (opcional): ")
    
    query = """
    INSERT INTO produto (nome, descricao, quantidade_estoque, valor, observacoes, id_vendedor)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (nome, descricao, estoque, valor, observacoes, id_vendedor)
    
    if execute_query(conn, query, params) is not None:
        print(f"[SUCESSO] Produto '{nome}' cadastrado com sucesso!")
    else:
        print("[ERRO] Falha ao cadastrar produto.")

def cadastrar_cliente(conn):
    """ADMIN: Cadastra um novo cliente."""
    if not check_permission(['Administrador']): return
    print("\n--- Adicionar Novo Cliente ---")
    
    nome = input("Nome do Cliente: ")
    try:
        data_nascimento = input("Data de Nascimento (AAAA-MM-DD): ")
        data_nasc_obj = datetime.strptime(data_nascimento, '%Y-%m-%d').date()
    except ValueError:
        print("[ERRO] Data inválida. Cancelando.")
        return

    sexo = input("Sexo (m/f/o): ").lower()
    
    today = date.today()
    idade = today.year - data_nasc_obj.year - ((today.month, today.day) < (data_nasc_obj.month, data_nasc_obj.day))

    query = "INSERT INTO cliente (nome, idade, sexo, data_nascimento) VALUES (%s, %s, %s, %s)"
    params = (nome, idade, sexo, data_nascimento)
    
    if execute_query(conn, query, params) is not None:
        print(f"[SUCESSO] Cliente '{nome}' cadastrado com sucesso!")
    else:
        print("[ERRO] Falha ao cadastrar cliente.")

# --- 5. Funções de Funcionário (Venda e Consulta) ---

def realizar_venda(conn):
    """FUNCIONARIO: Realiza uma venda com 1 produto e reduz o estoque."""
    if not check_permission(['Funcionario', 'Administrador']):
        return

    print("\n--- Realizar Venda ---")

    try:
        id_cliente = int(input("ID do Cliente: "))
        endereco = input("Endereço de Destino: ")
        id_transporte = input("ID da Transportadora (deixe vazio para NULA): ")
        id_transporte = int(id_transporte) if id_transporte.strip() else None
        id_produto = int(input("ID do Produto: "))
        qtd = int(input("Quantidade: "))
    except ValueError:
        print("[ERRO] Entrada inválida. Venda cancelada.")
        return

    # Buscar informações do produto
    produto_info = execute_query(
        conn,
        "SELECT valor, quantidade_estoque FROM produto WHERE id = %s",
        (id_produto,),
        fetch=True
    )
    if not produto_info:
        print(f"[ERRO] Produto ID {id_produto} não encontrado.")
        return

    if produto_info[0]['quantidade_estoque'] < qtd:
        print(f"[ERRO] Estoque insuficiente. Apenas {produto_info[0]['quantidade_estoque']} restantes.")
        return

    valor_unitario = produto_info[0]['valor']
    total_item = valor_unitario * qtd

    cursor = None
    try:
        # TENTA USAR A STORED PROCEDURE 'VENDA' (MÉTODO PREFERENCIAL)
        print("[INFO] Tentando registrar venda via Stored Procedure...")
        cursor = conn.cursor()
        
        # O callproc deve conter todos os parâmetros necessários para a SP registrar a venda por completo
        # (venda, item_venda e atualização de estoque).
        # Ajuste os parâmetros conforme a sua definição real da SP "Venda".
        # Exemplo: Venda(id_cliente, id_produto, qtd, total, endereco, id_transporte)
        cursor.callproc("Venda", (id_cliente, id_produto, qtd, id_transporte)) 
        
        conn.commit()
        
        # A SP não retorna o ID, então assumimos sucesso
        print("[SUCESSO] Venda realizada via Stored Procedure!")

    except Exception as e:
        # SE A SP FALHAR (por permissão, erro de sintaxe, etc.), USA O MÉTODO MANUAL COMO FALLBACK
        print(f"[AVISO] Falha ao executar SP Venda ({e}). Usando método manual...")
        conn.rollback() # Limpa qualquer falha parcial da SP
        cursor = None
        
        try:
            # MÉTODO MANUAL ------------------------------------------
            # 1. Criar venda
            cursor = conn.cursor()
            query_venda = """
                INSERT INTO venda (data_venda, hora_venda, valor, endereco, id_cliente, id_transporte)
                VALUES (CURDATE(), CURTIME(), %s, %s, %s, %s)
            """
            cursor.execute(query_venda, (total_item, endereco, id_cliente, id_transporte))
            id_venda = cursor.lastrowid
            conn.commit()
            cursor.close()
            cursor = None
            
            if not id_venda:
                raise Exception("Falha ao criar registro da venda manual.")

            # 2. Inserir item
            query_vp = "INSERT INTO venda_produto (id_venda, id_produto, qtd, valor) VALUES (%s, %s, %s, %s)"
            execute_query(conn, query_vp, (id_venda, id_produto, qtd, total_item))

            # 3. Diminuir estoque
            execute_query(conn, "UPDATE produto SET quantidade_estoque = quantidade_estoque - %s WHERE id = %s",
                          (qtd, id_produto))

            print(f"[SUCESSO] Venda (ID: {id_venda}) realizada manualmente! Total: R$ {total_item:.2f}")

        except Exception as e_manual:
             print(f"[ERRO] Falha completa ao processar a venda, mesmo manualmente: {e_manual}")
             conn.rollback()


    finally:
        if cursor:
            cursor.close()


def consultar_vendas(conn):
    """FUNCIONARIO: Consulta registros de venda (Últimas 10 vendas)."""
    if not check_permission(['Funcionario', 'Administrador']): return
    
    print("\n--- Consultar Registros de Venda (Últimas 10) ---")
    query = """
    SELECT 
        v.id, 
        v.data_venda, 
        v.valor, 
        c.nome AS cliente, 
        GROUP_CONCAT(CONCAT(p.nome, ' (', vp.qtd, 'x)')) AS produtos 
    FROM venda v 
    JOIN cliente c ON v.id_cliente = c.id 
    JOIN venda_produto vp ON v.id = vp.id_venda 
    JOIN produto p ON vp.id_produto = p.id 
    GROUP BY v.id 
    ORDER BY v.data_venda DESC 
    LIMIT 10
    """
    vendas = execute_query(conn, query, fetch=True)
    
    if vendas:
        print("\nID | Data | Valor Total | Cliente | Produtos Envolvidos")
        print("-" * 70)
        for v in vendas:
            produtos_display = (v['produtos'][:40] + '...') if len(v['produtos']) > 40 else v['produtos']
            print(f"{v['id']:<2} | {v['data_venda']} | R$ {v['valor']:<10.2f} | {v['cliente']:<15} | {produtos_display}")
    else:
        print("Nenhuma venda encontrada.")

# --- 6. Funções de Gerente (Busca, Edição, Apagar e Estatísticas) ---

def listar_tabelas(conn):
    """Retorna uma lista de todas as tabelas do banco de dados (Mais robusta)."""
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES;")
        tabelas = [t[0] for t in cursor.fetchall()]
    except Exception as e:
        print(f"[ERRO] Falha ao listar tabelas: {e}")
        tabelas = []
    finally:
        cursor.close()
    return tabelas
    
# --- FUNÇÃO MODIFICADA: Permite Gerente consultar todas as tabelas ---
def consultar_registros(conn):
    """GERENTE: Permite consultar e visualizar registros de todas as tabelas."""
    if not check_permission(['Gerente', 'Administrador']): return
    
    print("\n--- Consultar Registros (GERENTE) ---")
    
    # Chama a função genérica de visualização, permitindo que o Gerente escolha
    # qualquer tabela.
    visualizar_tabela(conn)

    input("\nPressione Enter para continuar...")


def editar_registro(conn):
    """Permite editar qualquer registro de qualquer tabela."""
    if not check_permission(['Gerente', 'Administrador']): return 
    
    tabelas = listar_tabelas(conn)
    if not tabelas:
        print("[ERRO] Nenhuma tabela encontrada no banco de dados.")
        return

    print("\n--- Tabelas disponíveis para EDIÇÃO ---")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")

    escolha = input("\nDigite o número da tabela que deseja editar (ou 0 para voltar): ").strip()
    if escolha == '0':
        return

    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        return

    tabela = tabelas[int(escolha) - 1]
    cursor = None # Inicializa para o bloco finally
    
    # 1. Mostrar registros atuais da tabela
    print("\n--- Registros Atuais ---")
    visualizar_tabela(conn, tabela) 
    
    try:
        cursor = conn.cursor()
        # 2. Obter colunas
        cursor.execute(f"DESCRIBE {tabela}")
        colunas_info = cursor.fetchall()
        colunas = [col[0] for col in colunas_info]
        
        if not colunas:
            print(f"[ERRO] A tabela {tabela} não tem colunas.")
            return

        id_coluna = colunas[0] # Assume que a primeira coluna é o ID

        id_editar = input(f"\nDigite o {id_coluna} do registro que deseja editar: ").strip()

        # 3. Obter dados atuais do registro
        cursor.execute(f"SELECT * FROM {tabela} WHERE {id_coluna} = %s", (id_editar,))
        registro_raw = cursor.fetchone()
        
        if not registro_raw:
            print("[ERRO] Registro não encontrado.")
            return
            
        # Converter para dicionário para facilitar o acesso por nome da coluna
        # É necessário garantir que o cursor não esteja em modo dictionary=True aqui,
        # ou ajustar a lógica. Mantendo a lógica de conversão manual.
        registro = dict(zip(colunas, registro_raw))


        # 4. Editar campos
        updates = []
        novos_valores = []
        
        for i, col in enumerate(colunas):
            if col == id_coluna:
                continue
            
            valor_atual = registro[col]
            
            novo_valor = input(f"Novo valor para {col} (atual: {valor_atual}) [Enter = manter]: ").strip()
            
            if novo_valor != "":
                updates.append(f"{col} = %s")
                novos_valores.append(novo_valor)

        if not updates:
            print("Nenhuma alteração feita.")
            return

        # 5. Atualizar no banco
        set_clause = ", ".join(updates)
        sql = f"UPDATE {tabela} SET {set_clause} WHERE {id_coluna} = %s"
        novos_valores.append(id_editar)

        cursor.execute(sql, novos_valores)
        conn.commit()
        print("[OK] Registro atualizado com sucesso!")
        
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    except Exception as e:
        print(f"[ERRO GERAL] {e}")
    finally:
        if cursor: # Fechamento seguro
            cursor.close()

# --- FUNÇÃO MODIFICADA: Permite Gerente apagar registro por ID em qualquer tabela ---
def apagar_registro(conn):
    """GERENTE / ADMIN: Apagar Registros (Linha por ID) de qualquer tabela."""
    if not check_permission(['Gerente', 'Administrador']): 
        return

    tabelas = listar_tabelas(conn)
    if not tabelas:
        print("[ERRO] Nenhuma tabela encontrada no banco de dados.")
        return

    print("\n--- Tabelas disponíveis para APAGAR REGISTRO POR ID ---")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")

    escolha = input("\nDigite o número da tabela que deseja gerenciar a exclusão (ou 0 para voltar): ").strip()
    if escolha == '0':
        return

    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        return

    tabela = tabelas[int(escolha) - 1]
    
    # 1. Mostrar registros atuais da tabela
    visualizar_tabela(conn, tabela) 

    # 2. Obter coluna ID
    cursor = None # Inicializa para o bloco finally
    try:
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {tabela}")
        colunas_info = cursor.fetchall()
        colunas = [col[0] for col in colunas_info]
        
        if not colunas:
            print(f"[ERRO] A tabela {tabela} não tem colunas.")
            return

        id_coluna = colunas[0] # Assume que a primeira coluna é o ID
    except Exception as e:
        print(f"[ERRO] Falha ao obter colunas da tabela {tabela}: {e}")
        return
    finally:
        if cursor:
            cursor.close()
        cursor = None # Limpa para a próxima utilização

    try:
        registro_id = int(input(f"\nDigite o {id_coluna} do registro que deseja APAGAR: "))
    except ValueError:
        print("[ERRO] ID inválido.")
        return

    confirm = input(f"ATENÇÃO: Confirma a exclusão do registro ID {registro_id} da tabela {tabela.upper()}? (s/n): ").lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    try:
        cursor = conn.cursor()
        # Apenas DELETE WHERE ID, sem TRUNCATE
        cursor.execute(f"DELETE FROM {tabela} WHERE {id_coluna} = %s", (registro_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"[SUCESSO] Registro (ID {registro_id}) da tabela '{tabela}' APAGADO com sucesso!")
        else:
            print(f"[AVISO] Nenhum registro encontrado com ID {registro_id}.")


    except mysql.connector.IntegrityError as err:
        if err.errno == 1451:  # Violação de chave estrangeira
            print(f"[ERRO] Não foi possível apagar: O registro está vinculado a outros dados no DB.")
        else:
            print(f"[ERRO] Falha ao apagar: {err}")
    except mysql.connector.Error as err:
        print(f"[ERRO] Erro no banco de dados: {err}")
    finally:
        if cursor:
            cursor.close()

def executar_reajuste(conn):
    """ADMIN: Executa Stored Procedure Reajuste."""
    if not check_permission(['Administrador']): return
    
    print("\n--- Executar Reajuste Salarial ---")
    cursor = None # Inicialização segura
    try:
        percentual = float(input("Digite o percentual de reajuste (ex: 5.5): "))
        categoria = input("Digite a categoria (vendedor, gerente, CEO): ").lower()
        
        if categoria not in ['vendedor', 'gerente', 'ceo']:
            print("[ERRO] Categoria inválida.")
            return

        # Chamada à Stored Procedure
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("Reajuste", (percentual, categoria))
        conn.commit()
        
        print(f"[SUCESSO] Reajuste de {percentual}% solicitado para a categoria {categoria.upper()}.")
            
    except ValueError:
        print("[ERRO] Percentual inválido.")
    except Exception as e:
        print(f"[ERRO] Falha ao executar Reajuste: {e}")
    finally:
        if cursor: # Fechamento seguro
            cursor.close()

def executar_sorteio(conn):
    """ADMIN: Executa Stored Procedure Sorteio. CORRIGIDO para múltiplos resultados de SP."""
    if not check_permission(['Administrador']): 
        return

    print("\n--- Executar Sorteio de Cliente (SP Sorteio) ---")
    cursor = None # Inicialização segura
    try:
        # Usa cursor.callproc para lidar melhor com Stored Procedures que retornam múltiplos conjuntos
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("Sorteio")

        sorteado = None
        # Itera sobre todos os conjuntos de resultados que o SP possa retornar
        for result_set in cursor.stored_results():
            dados = result_set.fetchall()
            if dados and 'cliente_sorteado' in dados[0]: # Procura pelo SELECT final com a coluna esperada
                sorteado = dados[0]
                break 
            
            # Se o SP retornar a mensagem "Sem clientes para sortear", captura a mensagem
            if dados and 'mensagem' in dados[0]:
                print(f"[INFO] {dados[0]['mensagem']}")
                return

        if sorteado:
            conn.commit() # Confirma o INSERT do voucher
            print("\nO cliente sorteado é:")
            print(f"  ID: {sorteado['cliente_sorteado']}")
            print(f"  Valor do Voucher: R$ {sorteado['valor_voucher']:.2f}")
        else:
            print("[INFO] Nenhum resultado de sorteio válido retornado. Verifique se há clientes cadastrados.")

    except Exception as e:
        print(f"[ERRO] Falha ao executar Sorteio: {e}")
    finally:
        if cursor: # Fechamento seguro
            cursor.close()


def executar_estatisticas(conn):
    """GERENTE: Executa Stored Procedure Estatísticas (com múltiplos SELECTs)."""
    if not check_permission(['Gerente', 'Administrador']):
        return

    print("\n--- Executar Estatísticas de Vendas (SP Estatísticas) ---")
    cursor = None # Inicialização segura

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.callproc("EstatisticasCompletas")

        resultado_idx = 1
        algum_resultado = False

        for result_set in cursor.stored_results():
            dados = result_set.fetchall()
            if not dados:
                continue

            algum_resultado = True
            print(f"\n[Conjunto #{resultado_idx}]")
            print("-" * 70)

            # Descobre os nomes das colunas retornadas dinamicamente
            colunas = list(dados[0].keys())
            print(" | ".join(colunas))
            print("-" * 70)

            # Imprime todas as linhas do conjunto
            for linha in dados:
                valores = [str(v) if v is not None else '-' for v in linha.values()]
                print(" | ".join(valores))

            resultado_idx += 1

        if not algum_resultado:
            print("[ERRO] Nenhum dado retornado pela procedure.")
        else:
            print("\n[INFO] Todas as estatísticas foram exibidas com sucesso.")

    except Exception as e:
        print(f"[ERRO] Falha ao executar Estatísticas: {e}")
        print("Detalhes: O usuário pode não ter permissão ou o SP pode estar ausente.")
    finally:
        if cursor: # Fechamento seguro
            cursor.close()


# --- 7. Funções Auxiliares (CRUD Genérico e Procedures) e Menus de Navegação ---


def cadastrar_generico(conn):
    """Permite inserir dados em qualquer tabela do banco."""
    if not check_permission(['Administrador']): return
    
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tabelas = [t[0] for t in cursor.fetchall()]

    print("\n--- Tabelas disponíveis ---")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")

    escolha = input("\nEscolha a tabela (ou 0 para voltar): ").strip()

    if escolha == "0":
        cursor.close()
        return
    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        cursor.close()
        return

    tabela = tabelas[int(escolha) - 1]

    # Obter estrutura da tabela
    cursor.execute(f"DESCRIBE {tabela}")
    colunas = cursor.fetchall()

    valores = []
    colunas_a_inserir = []
    
    for col in colunas:
        nome = col[0]
        tipo = col[1]
        extra = col[5] # Coluna 'Extra' contém 'auto_increment'

        # Ignora campos que são auto_increment ou explicitamente 'id'
        if "auto_increment" in extra or nome.lower() == "id":
            continue
            
        valor = input(f"Digite o valor para {nome} ({tipo}): ")
        valores.append(valor)
        colunas_a_inserir.append(nome) # Adiciona o nome da coluna para a query
        
    if not valores:
        print("[INFO] Nenhuma coluna para inserir encontrada (apenas IDs auto-incremento?).")
        cursor.close()
        return

    placeholders = ', '.join(['%s'] * len(valores))
    colunas_sql = ', '.join(colunas_a_inserir)
    sql = f"INSERT INTO {tabela} ({colunas_sql}) VALUES ({placeholders})"

    try:
        cursor.execute(sql, valores)
        conn.commit()
        print("[OK] Registro inserido com sucesso!")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()


def deletar_generico(conn):
    """Permite deletar todos os registros de uma tabela (TRUNCATE) ou uma linha específica (DELETE WHERE ID)."""
    if not check_permission(['Administrador']): return
    
    tabelas = listar_tabelas(conn)
    if not tabelas:
        print("[ERRO] Nenhuma tabela encontrada.")
        return

    print("\n--- SELEÇÃO DE TABELA PARA EXCLUSÃO ---")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")
    escolha = input("\nEscolha a tabela que deseja gerenciar a exclusão (ou 0 para voltar): ").strip()

    if escolha == '0':
        return
    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        return
    tabela = tabelas[int(escolha) - 1]

    # Novo menu de exclusão
    while True:
        clear_screen()
        print(f"--- OPÇÕES DE EXCLUSÃO PARA A TABELA '{tabela.upper()}' (ADMIN) ---")
        print("1. DELETAR TODOS OS REGISTROS (Limpar a Tabela Inteira - TRUNCATE TABLE) ⚠️")
        print("2. Deletar um registro específico (DELETE WHERE ID)")
        print("0. Voltar")
        
        op_del = input("\nEscolha a operação de exclusão: ").strip()

        if op_del == '1':
            # --- Opção 1: TRUNCATE TABLE (Apenas ADMIN) ---
            print(f"\n[ATENÇÃO] Você está prestes a DELETAR TODOS OS DADOS da tabela '{tabela.upper()}'!")
            print("Atenção: Esta ação limpa todos os registros e reseta o contador de ID (auto-incremento).")
            confirm = input("Confirme a exclusão total e permanente (s/n): ").lower()
            if confirm != 's':
                print("Operação cancelada.")
                time.sleep(1)
                break 
            
            cursor = None
            try:
                cursor = conn.cursor()
                # Desativa temporariamente a checagem de FK para TRUNCATE (boa prática)
                cursor.execute(f"SET FOREIGN_KEY_CHECKS = 0;")
                cursor.execute(f"TRUNCATE TABLE {tabela};")
                cursor.execute(f"SET FOREIGN_KEY_CHECKS = 1;")
                conn.commit()
                print(f"[OK] Todos os registros da tabela '{tabela.upper()}' foram deletados e o auto-incremento resetado.")
            except mysql.connector.Error as err:
                print(f"[ERRO SQL] {err}")
            finally:
                if cursor:
                    cursor.close()
            input("Pressione Enter para continuar...")
            break 
            
        elif op_del == '2':
            # --- Opção 2: DELETE WHERE ID (Deletar Linha) ---
            
            # Lista os registros da tabela para o usuário escolher o ID
            visualizar_tabela(conn, tabela) 
            
            id_registro = input("\nDigite o ID do registro que deseja deletar: ").strip()

            confirm = input(f"Tem certeza que deseja deletar o registro {id_registro} da tabela {tabela}? (s/n): ").lower()
            if confirm != 's':
                print("Operação cancelada.")
                time.sleep(1)
                break

            cursor = None
            try:
                cursor = conn.cursor()
                cursor.execute(f"DELETE FROM {tabela} WHERE id = %s", (id_registro,))
                conn.commit()
                print("[OK] Registro deletado com sucesso!")
            except mysql.connector.Error as err:
                print(f"[ERRO SQL] {err}")
            finally:
                if cursor:
                    cursor.close()
            input("Pressione Enter para continuar...")
            break 
            
        elif op_del == '0':
            break
        else:
            print("[ERRO] Opção inválida. Tente novamente.")
            time.sleep(1)

def calcular_idade(conn):
    """Executa a function Calcula_Idade(cliente_id)."""
    if not check_permission(['Administrador']): return
    cursor = None # Inicialização segura (CORREÇÃO DE ATRIBUTO)
    try:
        cliente_id = int(input("Digite o ID do cliente: "))
        cursor = conn.cursor()
        cursor.execute(f"SELECT Calcula_Idade(%s);", (cliente_id,))
        idade = cursor.fetchone()[0]
        print(f"A idade do cliente (ID={cliente_id}) é {idade} anos.")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    except ValueError:
        print("[ERRO] ID do cliente inválido.")
    finally:
        # Fechamento seguro (CORREÇÃO DE ATRIBUTO)
        if cursor: 
            cursor.close()

def somar_frete(conn):
    """Executa a function Soma_Frete(venda_id)."""
    if not check_permission(['Administrador']): return
    cursor = None # Inicialização segura (CORREÇÃO DE ATRIBUTO)
    try:
        venda_id = int(input("Digite o ID da venda: "))
        cursor = conn.cursor()
        # Nota: A função Soma_Frete pode não existir no SQL provido
        cursor.execute(f"SELECT Soma_Frete(%s);", (venda_id,))
        frete = cursor.fetchone()[0]
        print(f"O frete total da venda (ID={venda_id}) é R$ {frete:.2f}.")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    except ValueError:
        print("[ERRO] ID da venda inválido.")
    finally:
        if cursor: # Fechamento seguro (CORREÇÃO DE ATRIBUTO)
            cursor.close()

def calcular_arrecadado(conn):
    """Executa a function Arrecadado(data, id_vendedor) que calcula total de vendas."""
    if not check_permission(['Administrador']): return
    cursor = None # Inicialização segura (CORREÇÃO DE ATRIBUTO)
    try:
        # A função Arrecadado no SQL espera 2 argumentos (data, id_vendedor).
        print("Para usar Arrecadado(data, id_vendedor) é necessário fornecer os parâmetros.")
        data_param = input("Digite a data (AAAA-MM-DD): ")
        id_vendedor_param = int(input("Digite o ID do Vendedor: "))

        cursor = conn.cursor()
        # CORREÇÃO: Chamando como FUNCTION (SELECT) e não como PROCEDURE (CALL)
        cursor.execute(f"SELECT Arrecadado(%s, %s);", (data_param, id_vendedor_param))
        total_arrecadado = cursor.fetchone()[0]

        if total_arrecadado is not None:
             print(f"Valor total arrecadado na data {data_param} pelo vendedor {id_vendedor_param}: R$ {total_arrecadado:.2f}")
        else:
             print("[INFO] Nenhum valor arrecadado retornado.")
             
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    except ValueError:
        print("[ERRO] Entrada de parâmetros inválida.")
    finally:
        if cursor: # Fechamento seguro (CORREÇÃO DE ATRIBUTO)
            cursor.close()


def visualizar_tabela(conn, tabela_selecionada=None):
    """Permite ao ADMIN/GERENTE visualizar qualquer tabela do banco, ou uma específica."""
    if not conn or not conn.is_connected():
        print("[ERRO] Conexão com o banco está inativa.")
        return []

    if not check_permission(['Administrador', 'Gerente', 'Funcionario']): return
    
    cursor = conn.cursor()

    # Obter todas as tabelas do banco de dados atual
    cursor.execute("SHOW TABLES;")
    tabelas = [t[0] for t in cursor.fetchall()]

    if not tabelas:
        print("[AVISO] Nenhuma tabela encontrada no banco de dados.")
        cursor.close()
        return []
    
    # Se a tabela não foi selecionada (chamada do menu Admin/Gerente), o usuário escolhe
    if not tabela_selecionada:
        print("\n--- Tabelas disponíveis para Consulta ---")
        for i, tabela in enumerate(tabelas, start=1):
            print(f"{i}. {tabela}")

        escolha = input("\nDigite o número da tabela que deseja visualizar (ou 0 para voltar): ").strip()
        if escolha == '0':
            cursor.close()
            return tabelas 

        try:
            idx = int(escolha) - 1
            if idx < 0 or idx >= len(tabelas):
                print("[ERRO] Escolha inválida.")
                cursor.close()
                return tabelas
            tabela_selecionada = tabelas[idx]
        except ValueError:
            print("[ERRO] Escolha inválida.")
            cursor.close()
            return tabelas

    # Buscar dados da tabela
    try:
        cursor.execute(f"SELECT * FROM {tabela_selecionada};")
        registros = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        print(f"\n--- Conteúdo da tabela '{tabela_selecionada}' ---")
        if not registros:
            print("[VAZIO] Nenhum registro encontrado.")
        else:
            # Usando tabulate para uma saída mais formatada
            data_list = []
            for linha in registros:
                data_list.append([str(c) if c is not None else 'NULL' for c in linha])
                
            print(tabulate(data_list, headers=colunas, tablefmt="grid"))
            
    except Exception as e:
        print(f"[ERRO] Não foi possível exibir a tabela: {e}")

    cursor.close()
    return tabelas 
    
# -------------------------------------------------------------
# Os menus abaixo usam as funções corrigidas acima e na Seção 6.
# -------------------------------------------------------------

def menu_admin(conn):
    """Menu para o Administrador (todas as permissões do sistema)."""
    while True:
        clear_screen()
        print(f"--- MENU ADMINISTRADOR (Usuário: {CURRENT_USER}) ---")
        print("1. Criar / Preencher Dados Nativos (Reinicializar banco)")
        print("2. Gerenciar Registros (CRUD Completo)")  
        print("3. Executar Procedures e Funções de Gestão")
        print("--- CONSULTAS LIVRES ---")
        print("4. Visualizar qualquer tabela do banco")
        print("0. Sair e Fazer Logout")

        choice = input("\nEscolha uma opção: ").strip()

        # ---------------------------
        # 1) CRIAR / REINICIAR DB
        # ---------------------------
        if choice == '1':
            criar_e_destruir_db()
            # input("Pressione Enter para continuar...") # Removido pois já está em criar_e_destruir_db

        # ---------------------------
        # 2) CRUD COMPLETO
        # ---------------------------
        elif choice == '2':
            while True:
                clear_screen()
                print("--- GERENCIAR REGISTROS (CRUD) ---")
                print("1. Adicionar Registro (Genérico)")
                print("2. Editar Registro (Genérico)")
                print("3. Deletar Registro (TRUNCATE ou DELETE WHERE ID)")
                print("4. Voltar")
                sub_choice = input("Opção: ").strip()

                if sub_choice == '1':
                    cadastrar_generico(conn)  
                elif sub_choice == '2':
                    editar_registro(conn)  
                elif sub_choice == '3':
                    deletar_generico(conn)  
                elif sub_choice == '4':
                    break
                else:
                    print("[ERRO] Opção inválida."); time.sleep(1)
                
                input("Pressione Enter para continuar...")
                if sub_choice not in ['1', '2', '3']: break # Sai do sub-menu se não for CRUD


        # ---------------------------
        # 3) PROCEDURES E FUNÇÕES
        # ---------------------------
        elif choice == '3':
            while True:
                clear_screen()
                print("--- PROCEDURES E FUNÇÕES DE GESTÃO ---")
                print("1. Reajuste Salarial (Procedure Reajuste)")
                print("2. Calcular Idade de um Cliente (Function Calcula_Idade)")
                print("3. Somar Frete (Function Soma_Frete)")
                print("4. Executar Sorteio de Cliente (SP Sorteio)")
                print("5. Calcular Valor Arrecadado Total (Function Arrecadado)")
                print("6. Estatísticas Gerais (Procedure Estatisticas)")
                print("7. Registrar Venda (Procedure Venda)")
                print("0. Voltar")
                sub_choice = input("Escolha uma opção: ").strip()

                if sub_choice == '1':
                    executar_reajuste(conn)
                elif sub_choice == '2':
                    calcular_idade(conn) 
                elif sub_choice == '3':
                    somar_frete(conn) 
                elif sub_choice == '4':
                    executar_sorteio(conn)
                elif sub_choice == '5':
                    calcular_arrecadado(conn) 
                elif sub_choice == '6':
                    executar_estatisticas(conn)
                elif sub_choice == '7':
                    realizar_venda(conn)
                elif sub_choice == '0':
                    break
                else:
                    print("[ERRO] Opção inválida."); time.sleep(1)
                
                input("Pressione Enter para continuar...")
                if sub_choice == '0': break


        # ---------------------------
        # 4) CONSULTAS LIVRES 
        # ---------------------------
        elif choice == '4':
            visualizar_tabela(conn) # Chama a função genérica sem parâmetro
            input("Pressione Enter para continuar...")

        # ---------------------------
        # 0) SAIR
        # ---------------------------
        elif choice == '0':
            break

        else:
            print("[ERRO] Opção inválida.")
            time.sleep(1)

# --- FUNÇÃO MODIFICADA: Gerente agora tem CRUD (sem TRUNCATE) em todas as tabelas ---
def menu_gerente(conn):
    """Menu para o Gerente (Busca, Edição, Apagar por ID, Estatísticas)."""
    if not check_permission(['Gerente', 'Administrador']): return
    while True:
        clear_screen()
        print(f"--- MENU GERENTE (Usuário: {CURRENT_USER}) ---")
        print("--- CRUD (Todas as Tabelas) ---")
        print("1. Consultar Registros")
        print("2. Editar Registro (por ID)")
        print("3. Apagar Registro (por ID)")
        print("--- CONSULTA AVANÇADA ---")
        print("4. Executar Estatísticas de Vendas")
        print("0. Voltar ao Menu Principal / Sair")
        
        choice = input("\nEscolha uma opção: ").strip()

        if choice == '1': consultar_registros(conn)
        elif choice == '2': editar_registro(conn)
        elif choice == '3': apagar_registro(conn)
        elif choice == '4': executar_estatisticas(conn)
        elif choice == '0': break
        else: print("[ERRO] Opção inválida."); time.sleep(1); continue
            
        input("\nPressione Enter para continuar...")

def menu_funcionario(conn):
    """Menu para o Funcionário (Adição de Venda e Consulta de Vendas)."""
    if not check_permission(['Funcionario', 'Administrador']): return
    while True:
        clear_screen()
        print(f"--- MENU FUNCIONÁRIO (Usuário: {CURRENT_USER}) ---")
        print("1. Realizar Nova Venda (Adicionar Registro)")
        print("2. Consultar Registros de Venda")
        print("0. Voltar ao Menu Principal / Sair")
        
        choice = input("\nEscolha uma opção: ").strip()

        if choice == '1': realizar_venda(conn)
        elif choice == '2': consultar_vendas(conn)
        elif choice == '0': break
        else: print("[ERRO] Opção inválida."); time.sleep(1); continue
            
        input("\nPressione Enter para continuar...")

def menu_principal(conn):
    """Direciona para o menu específico com base no papel do usuário."""
    role = get_user_role()
    if role == 'Administrador':
        menu_admin(conn)
    elif role == 'Gerente':
        menu_gerente(conn)
    elif role == 'Funcionario':
        menu_funcionario(conn)
    else:
        print("Você está logado, mas não tem acesso a nenhum menu.")
        time.sleep(2)

# --- 8. Função Principal (Login) ---

def login():
    """Realiza o login e inicia o sistema."""
    global CURRENT_USER, CURRENT_PASSWORD
    clear_screen()
    print("==============================================")
    print("   SISTEMA DE E-COMMERCE - ACESSO RESTRITO    ")
    print("==============================================")
    
    CURRENT_USER = input("Digite o Usuário MySQL (ex: admin, gerente, funcionario): ").strip()
    CURRENT_PASSWORD = input("Digite a Senha do MySQL: ").strip()

    conn = get_db_connection()
    if conn:
        print(f"\n[SUCESSO] Conexão estabelecida como {get_user_role()} ({CURRENT_USER}).")
        menu_principal(conn)
        conn.close()
    else:
        print("\n[ERRO] Falha na conexão ou credenciais inválidas. Tente novamente.")
        time.sleep(2)

if __name__ == '__main__':
    while True:
        login()
        clear_screen()
        print("Sessão encerrada.")
        if input("Deseja logar novamente? (s/n): ").lower() != 's':
            break
