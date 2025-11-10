import mysql.connector
from datetime import date, datetime
from conexao import conectar
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

    cursor = conn.cursor()

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
    cursor.executemany(query_func, funcionarios_data)
    conn.commit()
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
    cursor.executemany(query_cliente, clientes_data)
    conn.commit()
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
    cursor.executemany(query_produto, produtos_data)
    conn.commit()
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
    cursor.execute(query_transp)
    conn.commit()
    print("> 5 transportadoras inseridas com sucesso.")

    cursor.close()
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
        try:
            preencher_dados_nativos(conn)
            print("> Dados nativos inseridos com sucesso!")
        except TypeError as te:
            print(f"[ERRO DE TIPO] Verifique o uso de execute/executemany em 'preencher_dados_nativos': {te}")
        except Exception as e:
            print(f"[ERRO] Ocorreu um erro ao preencher os dados nativos: {e}")

        conn.commit()

    except Exception as e:
        print(f"[ERRO GERAL] Erro durante a tentativa de preenchimento: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
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

    try:
        # Criar venda
        query_venda = """
            INSERT INTO venda (data_venda, hora_venda, valor, endereco, id_cliente, id_transporte)
            VALUES (CURDATE(), CURTIME(), %s, %s, %s, %s)
        """
        id_venda = execute_query(conn, query_venda, (total_item, endereco, id_cliente, id_transporte))
        if not id_venda:
            raise Exception("Falha ao criar registro da venda.")

        # Inserir item
        query_vp = "INSERT INTO venda_produto (id_venda, id_produto, qtd, valor) VALUES (%s, %s, %s, %s)"
        execute_query(conn, query_vp, (id_venda, id_produto, qtd, total_item))

        # Diminuir estoque
        try:
            execute_query(conn, "CALL Venda(%s, %s, %s, %s)", (id_cliente, id_produto, qtd, id_transporte))
        except Exception:
            execute_query(conn, "UPDATE produto SET quantidade_estoque = quantidade_estoque - %s WHERE id = %s",
                          (qtd, id_produto))

        print(f"[SUCESSO] Venda (ID: {id_venda}) realizada! Total: R$ {total_item:.2f}")

    except Exception as e:
        print(f"[ERRO] Erro ao processar a venda: {e}")


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

def editar_registro(conn):
    """GERENTE: Edição de Registros (Clientes, Produtos, Vendedores)."""
    if not check_permission(['Gerente', 'Administrador']):
        return

    print("\n--- Editar Registros (GERENTE) ---")
    print("1. Editar Produto | 2. Editar Cliente | 3. Editar Vendedor")
    escolha = input("Selecione a tabela (1/2/3): ").strip()

    if escolha not in ['1', '2', '3']:
        print("[ERRO] Opção inválida.")
        return

    tabela = ['produto', 'cliente', 'vendedor'][int(escolha) - 1]

    try:
        registro_id = int(input(f"Digite o ID do {tabela} a ser editado: "))
    except ValueError:
        print("[ERRO] ID inválido.")
        return

    # Obter colunas da tabela
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {tabela};")
    colunas = [row[0] for row in cursor.fetchall()]
    cursor.close()

    print("\nCampos disponíveis para edição:")
    print(", ".join(colunas))
    campo = input("Digite o nome EXATO do campo a ser alterado: ").strip().lower()

    if campo not in colunas:
        print(f"[ERRO] O campo '{campo}' não existe na tabela '{tabela}'.")
        return

    novo_valor = input(f"Digite o novo valor para o campo '{campo}': ").strip()

    # Conversão automática de tipo
    try:
        if campo in ['valor', 'salario', 'cashback', 'nota_media']:
            novo_valor = float(novo_valor)
        elif campo in ['quantidade_estoque', 'idade', 'id_vendedor']:
            novo_valor = int(novo_valor)
    except ValueError:
        print("[ERRO] Tipo de valor inválido.")
        return

    try:
        cursor = conn.cursor()
        query = f"UPDATE {tabela} SET {campo} = %s WHERE id = %s"
        cursor.execute(query, (novo_valor, registro_id))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"[SUCESSO] {tabela.capitalize()} (ID {registro_id}) atualizado com sucesso!")
        else:
            print(f"[ERRO] Nenhum registro com ID {registro_id} encontrado.")

        cursor.close()
    except Exception as e:
        print(f"[ERRO] Falha ao editar registro: {e}")


def consultar_registros(conn):
    """GERENTE: Busca Produtos, Clientes ou Vendedores (por ID ou nome)."""
    if not check_permission(['Gerente', 'Administrador']):
        return

    print("\n--- Buscar Registros (GERENTE) ---")
    print("1. Buscar Produtos | 2. Buscar Clientes | 3. Buscar Vendedores")
    escolha = input("Selecione a tabela (1/2/3): ").strip()

    if escolha not in ['1', '2', '3']:
        print("[ERRO] Opção inválida.")
        return

    tabela = ['produto', 'cliente', 'vendedor'][int(escolha) - 1]
    termo = input(f"Digite o ID ou parte do nome do {tabela}: ").strip()

    cursor = conn.cursor(dictionary=True)
    try:
        # Busca por ID se for número
        if termo.isdigit():
            query = f"SELECT * FROM {tabela} WHERE id = %s"
            cursor.execute(query, (int(termo),))
        else:
            query = f"SELECT * FROM {tabela} WHERE nome LIKE %s LIMIT 10"
            cursor.execute(query, (f'%{termo}%',))

        resultados = cursor.fetchall()

        if resultados:
            print(f"\nResultados encontrados na tabela {tabela.upper()}:")

            # Exibição formatada (tabela)
            print(tabulate(resultados, headers="keys", tablefmt="grid", numalign="center", stralign="center"))
        else:
            print(f"[AVISO] Nenhum registro encontrado em {tabela}.")
    except Exception as e:
        print(f"[ERRO] Falha ao consultar registros: {e}")
    finally:
        cursor.close()



def apagar_registro(conn):
    """GERENTE / ADMIN: Apagar Registros (Clientes, Produtos, Vendedores)."""
    if not check_permission(['Gerente', 'Administrador']): 
        return

    print("\n--- Apagar Registros (GERENTE/ADMIN) ---")
    print("1. Apagar Produto | 2. Apagar Cliente | 3. Apagar Vendedor")
    escolha = input("Selecione a tabela (1/2/3): ").strip()

    tabelas = {
        '1': ('produto', 'nome'),
        '2': ('cliente', 'nome'),
        '3': ('vendedor', 'nome')
    }

    if escolha not in tabelas:
        print("[ERRO] Opção inválida.")
        return

    tabela, campo_nome = tabelas[escolha]

    try:
        registro_id = int(input(f"Digite o ID do {tabela} a ser APAGADO: "))
    except ValueError:
        print("[ERRO] ID inválido.")
        return

    # Buscar o nome do registro antes de excluir (para confirmar)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT {campo_nome} FROM {tabela} WHERE id = %s", (registro_id,))
    registro = cursor.fetchone()

    if not registro:
        print(f"[ERRO] Nenhum {tabela} encontrado com ID {registro_id}.")
        return

    nome_registro = registro[campo_nome]
    confirm = input(f"ATENÇÃO: Confirma a exclusão de {tabela.upper()} '{nome_registro}' (ID {registro_id})? (s/n): ").lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    try:
        cursor.execute(f"DELETE FROM {tabela} WHERE id = %s", (registro_id,))
        conn.commit()
        print(f"[SUCESSO] {tabela.capitalize()} '{nome_registro}' (ID {registro_id}) APAGADO com sucesso!")

    except mysql.connector.IntegrityError as err:
        if err.errno == 1451:  # Violação de chave estrangeira
            print(f"[ERRO] Não foi possível apagar: o {tabela} '{nome_registro}' está vinculado a outros registros (ex: vendas).")
        else:
            print(f"[ERRO] Falha ao apagar: {err}")
    except mysql.connector.Error as err:
        print(f"[ERRO] Erro no banco de dados: {err}")
    finally:
        cursor.close()
        
def executar_reajuste(conn):
    """ADMIN: Executa Stored Procedure Reajuste."""
    if not check_permission(['Administrador']): return
    
    print("\n--- Executar Reajuste Salarial ---")
    try:
        percentual = float(input("Digite o percentual de reajuste (ex: 5.5): "))
        categoria = input("Digite a categoria (vendedor, gerente, CEO): ").lower()
        
        if categoria not in ['vendedor', 'gerente', 'ceo']:
            print("[ERRO] Categoria inválida.")
            return

        query = "CALL Reajuste(%s, %s)"
        resultados = execute_query(conn, query, (percentual, categoria), fetch=True)
        
        if resultados:
            print(f"[SUCESSO] {resultados[0]['resultado']}")
        else:
            print("[ERRO] Falha ao executar Reajuste. Verifique os parâmetros e se o SP existe.")
            
    except ValueError:
        print("[ERRO] Percentual inválido.")

def executar_sorteio(conn):
    """ADMIN: Executa Stored Procedure Sorteio."""
    if not check_permission(['Administrador']): 
        return

    print("\n--- Executar Sorteio de Cliente (SP Sorteio) ---")
    query = "CALL Sorteio()"
    resultados = execute_query(conn, query, fetch=True)

    if resultados:
        sorteado = resultados[0]
        print("\nO cliente sorteado é:")
        print(f"  ID: {sorteado['cliente_sorteado']}")
        print(f"  Valor do Voucher: R$ {sorteado['valor_voucher']:.2f}")
    else:
        print("[ERRO] Falha ao executar Sorteio. Verifique se o SP existe.")


def executar_estatisticas(conn):
    """GERENTE: Executa Stored Procedure Estatísticas (com múltiplos SELECTs)."""
    if not check_permission(['Gerente', 'Administrador']):
        return

    print("\n--- Executar Estatísticas de Vendas (SP Estatísticas) ---")

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
        cursor.close()


# --- 7. Menus de Navegação ---

def menu_admin(conn):
    """Menu para o Administrador (todas as permissões do sistema)."""
    while True:
        clear_screen()
        print(f"--- MENU ADMINISTRADOR (Usuário: {CURRENT_USER}) ---")
        print("1. Criar / Preencher Dados Nativos (Reinicializar banco)")
        print("2. Gerenciar Registros (CRUD Completo)")  
        print("3. Executar Procedures e Funções de Gestão")
        print("4. Executar Sorteio de Cliente")
        print("--- ACESSAR OUTROS MENUS ---")
        print("5. Abrir Menu do Gerente")
        print("6. Abrir Menu do Funcionário")
        print("--- CONSULTAS LIVRES ---")
        print("7. Visualizar qualquer tabela do banco")
        print("0. Sair e Fazer Logout")

        choice = input("\nEscolha uma opção: ").strip()

        # ---------------------------
        # 1) CRIAR / REINICIAR DB
        # ---------------------------
        if choice == '1':
            criar_e_destruir_db()
            input("Pressione Enter para continuar...")

        # ---------------------------
        # 2) CRUD COMPLETO
        # ---------------------------
        elif choice == '2':
            clear_screen()
            print("--- GERENCIAR REGISTROS (CRUD) ---")
            print("1. Adicionar Registro")
            print("2. Editar Registro")
            print("3. Deletar Registro")
            print("4. Voltar")
            sub_choice = input("Opção: ").strip()

            if sub_choice == '1':
                cadastrar_generico(conn)  # Permite inserir em qualquer tabela
            elif sub_choice == '2':
                editar_registro(conn)  # Permite editar qualquer registro
            elif sub_choice == '3':
                deletar_generico(conn)  # Permite deletar qualquer registro
            input("Pressione Enter para continuar...")

        # ---------------------------
        # 3) PROCEDURES E FUNÇÕES
        # ---------------------------
        elif choice == '3':
            clear_screen()
            print("--- PROCEDURES E FUNÇÕES DE GESTÃO ---")
            print("1. Reajuste Salarial (Procedure Reajuste)")
            print("2. Calcular Idade de um Cliente (Function Calcula_Idade)")
            print("3. Somar Frete (Function Soma_Frete)")
            print("4. Calcular Valor Arrecadado Total (Procedure Arrecadado)")
            print("5. Estatísticas Gerais (Procedure Estatisticas)")
            print("6. Registrar Venda (Procedure Venda)")
            print("0. Voltar")
            sub_choice = input("Escolha uma opção: ").strip()

            if sub_choice == '1':
                executar_reajuste(conn)
            elif sub_choice == '2':
                calcular_idade(conn)
            elif sub_choice == '3':
                somar_frete(conn)
            elif sub_choice == '4':
                calcular_arrecadado(conn)
            elif sub_choice == '5':
                executar_estatisticas(conn)
            elif sub_choice == '6':
                realizar_venda(conn)
            input("Pressione Enter para continuar...")

        # ---------------------------
        # 4) SORTEIO CLIENTE
        # ---------------------------
        elif choice == '4':
            executar_sorteio(conn)
            input("Pressione Enter para continuar...")

        # ---------------------------
        # 5) MENU GERENTE
        # ---------------------------
        elif choice == '5':
            menu_gerente(conn)

        # ---------------------------
        # 6) MENU FUNCIONÁRIO
        # ---------------------------
        elif choice == '6':
            menu_funcionario(conn)

        # ---------------------------
        # 7) CONSULTAS LIVRES
        # ---------------------------
        elif choice == '7':
            visualizar_tabela(conn)
            input("Pressione Enter para continuar...")

        # ---------------------------
        # 0) SAIR
        # ---------------------------
        elif choice == '0':
            break

        else:
            print("[ERRO] Opção inválida.")
            time.sleep(1)

def cadastrar_generico(conn):
    """Permite inserir dados em qualquer tabela do banco."""
    tabelas = visualizar_tabela(conn)
    print("\nTabelas disponíveis:")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")
    escolha = input("Escolha a tabela: ").strip()

    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        return
    tabela = tabelas[int(escolha) - 1]

    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {tabela}")
    colunas = cursor.fetchall()

    valores = []
    for col in colunas:
        nome = col[0]
        tipo = col[1]
        if "auto_increment" in col[5] or nome.lower() == "id":
            continue
        valor = input(f"Digite o valor para {nome} ({tipo}): ")
        valores.append(valor)

    placeholders = ', '.join(['%s'] * len(valores))
    colunas_sql = ', '.join([c[0] for c in colunas if not ("auto_increment" in c[5] or c[0].lower() == "id")])
    sql = f"INSERT INTO {tabela} ({colunas_sql}) VALUES ({placeholders})"

    try:
        cursor.execute(sql, valores)
        conn.commit()
        print("[OK] Registro inserido com sucesso!")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()

def editar_registro(conn):
    """Permite editar qualquer registro de qualquer tabela."""
    tabelas = visualizar_tabela(conn)
    print("\nTabelas disponíveis:")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")
    escolha = input("Escolha a tabela: ").strip()

    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        return
    tabela = tabelas[int(escolha) - 1]

    id_registro = input("Digite o ID do registro que deseja editar: ").strip()

    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE {tabela}")
    colunas = cursor.fetchall()

    updates = []
    valores = []

    for col in colunas:
        nome = col[0]
        if nome.lower() == "id":
            continue
        novo_valor = input(f"Novo valor para {nome} (deixe vazio para não alterar): ").strip()
        if novo_valor != "":
            updates.append(f"{nome} = %s")
            valores.append(novo_valor)

    if not updates:
        print("Nenhuma alteração feita.")
        return

    sql = f"UPDATE {tabela} SET {', '.join(updates)} WHERE id = %s"
    valores.append(id_registro)

    try:
        cursor.execute(sql, valores)
        conn.commit()
        print("[OK] Registro atualizado com sucesso!")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()

def deletar_generico(conn):
    """Permite deletar registros de qualquer tabela."""
    tabelas = visualizar_tabela(conn)
    print("\nTabelas disponíveis:")
    for i, t in enumerate(tabelas, 1):
        print(f"{i}. {t}")
    escolha = input("Escolha a tabela: ").strip()

    if not escolha.isdigit() or int(escolha) < 1 or int(escolha) > len(tabelas):
        print("[ERRO] Escolha inválida.")
        return
    tabela = tabelas[int(escolha) - 1]

    visualizar_tabela(conn, tabela)
    id_registro = input("Digite o ID do registro que deseja deletar: ").strip()

    confirm = input(f"Tem certeza que deseja deletar o registro {id_registro} da tabela {tabela}? (s/n): ").lower()
    if confirm != 's':
        print("Operação cancelada.")
        return

    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {tabela} WHERE id = %s", (id_registro,))
        conn.commit()
        print("[OK] Registro deletado com sucesso!")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()

def calcular_idade(conn):
    """Executa a function Calcula_Idade(cliente_id)."""
    try:
        cliente_id = int(input("Digite o ID do cliente: "))
        cursor = conn.cursor()
        cursor.execute(f"SELECT Calcula_Idade({cliente_id});")
        idade = cursor.fetchone()[0]
        print(f"A idade do cliente (ID={cliente_id}) é {idade} anos.")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()

def somar_frete(conn):
    """Executa a function Soma_Frete(venda_id)."""
    try:
        venda_id = int(input("Digite o ID da venda: "))
        cursor = conn.cursor()
        cursor.execute(f"SELECT Soma_Frete({venda_id});")
        frete = cursor.fetchone()[0]
        print(f"O frete total da venda (ID={venda_id}) é R$ {frete:.2f}.")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()

def calcular_arrecadado(conn):
    """Executa a procedure Arrecadado() que calcula total de vendas."""
    try:
        cursor = conn.cursor()
        cursor.callproc("Arrecadado")
        for result in cursor.stored_results():
            rows = result.fetchall()
            for row in rows:
                print(f"Valor total arrecadado: R$ {row[0]:.2f}")
    except mysql.connector.Error as err:
        print(f"[ERRO SQL] {err}")
    finally:
        cursor.close()


def visualizar_tabela(conn):
    """Permite ao ADMIN visualizar qualquer tabela do banco."""
    if not conn or not conn.is_connected():
        print("[ERRO] Conexão com o banco está inativa.")
        return

    cursor = conn.cursor()

    # Obter todas as tabelas do banco de dados atual
    cursor.execute("SHOW TABLES;")
    tabelas = [t[0] for t in cursor.fetchall()]

    if not tabelas:
        print("[AVISO] Nenhuma tabela encontrada no banco de dados.")
        cursor.close()
        return

    print("\n--- Tabelas disponíveis ---")
    for i, tabela in enumerate(tabelas, start=1):
        print(f"{i}. {tabela}")

    escolha = input("\nDigite o número da tabela que deseja visualizar (ou 0 para voltar): ").strip()
    if escolha == '0':
        cursor.close()
        return

    try:
        idx = int(escolha) - 1
        if idx < 0 or idx >= len(tabelas):
            print("[ERRO] Escolha inválida.")
            cursor.close()
            return
        tabela_selecionada = tabelas[idx]

        # Buscar dados da tabela
        cursor.execute(f"SELECT * FROM {tabela_selecionada};")
        registros = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]

        print(f"\n--- Conteúdo da tabela '{tabela_selecionada}' ---")
        if not registros:
            print("[VAZIO] Nenhum registro encontrado.")
        else:
            # Exibir cabeçalho
            print(" | ".join(colunas))
            print("-" * 80)
            for linha in registros:
                print(" | ".join(str(c) for c in linha))
    except Exception as e:
        print(f"[ERRO] Não foi possível exibir a tabela: {e}")

    cursor.close()


def menu_gerente(conn):
    """Menu para o Gerente (Busca, Edição, Apagar, Estatísticas)."""
    if not check_permission(['Gerente', 'Administrador']): return
    while True:
        clear_screen()
        print(f"--- MENU GERENTE (Usuário: {CURRENT_USER}) ---")
        print("--- CRUD ---")
        # ampliar as tabelas que o gerente tem acesso
        print("1. Buscar Registros (Clientes/Produtos/Vendedores)")
        print("2. Editar Registro (Cliente/Produto/Vendedor)")
        print("3. Apagar Registro (Cliente/Produto/Vendedor)")
        print("--- CONSULTA ---")
        # colocar as outras execuções aqui
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