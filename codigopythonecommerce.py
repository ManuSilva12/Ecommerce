import mysql.connector
from datetime import date, datetime
from conexao import conectar
import random
import os
import time
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
    """Executa uma query no banco de dados e lida com erros de permissão."""
    cursor = None
    try:
        cursor = conn.cursor(dictionary=True) 
        cursor.execute(query, params or ())
        
        if fetch:
            results = []
            if cursor.with_rows:
                results.extend(cursor.fetchall())

            for result in cursor.stored_results(): 
                results.extend(result.fetchall())
            
            return results
        else:
            conn.commit()
            return cursor.lastrowid
    except mysql.connector.Error as err:
        print(f"\n[ERRO] Erro de SQL: {err}")
        if 'denied' in str(err).lower():
            print(f"Detalhes: O usuário '{CURRENT_USER}' pode não ter permissão para esta ação.")
        if conn:
            conn.rollback()
        return None
    finally:
        if cursor:
            cursor.close()

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

    # Inserir Vendedores (Papéis essenciais)
    vendedores_data = [
        ('Vendedor Essencial', 2000.00, 'vendedor', 'Causa Padrao A', 4.5), 
        ('Gerente Essencial', 5000.00, 'gerente', 'Causa Padrao B', 4.8), 
        ('Admin Essencial', 15000.00, 'CEO', 'Causa Padrao C', 5.0),
    ]
    query_vendedor = "INSERT INTO vendedor (nome, salario, tipo, causa_social, nota_media) VALUES (%s, %s, %s, %s, %s)"
    execute_query(conn, query_vendedor, vendedores_data)

    # Inserir Clientes
    clientes_data = []
    for i in range(1, 6):
        nome = f"Cliente {i}"
        idade = random.randint(18, 60)
        sexo = random.choice(['m', 'f', 'o'])
        ano = 2025 - idade
        data_nascimento = date(year=ano, month=random.randint(1, 12), day=random.randint(1, 28))
        clientes_data.append((nome, idade, sexo, data_nascimento))

    query_cliente = "INSERT INTO cliente (nome, idade, sexo, data_nascimento) VALUES (%s, %s, %s, %s)"
    cursor = conn.cursor()
    cursor.executemany(query_cliente, clientes_data)
    conn.commit()
    cursor.close()

    # Inserir Clientes Especiais (para teste de Sorteio SP)
    query_esp = "INSERT INTO cliente_especial (id_cliente, cashback, data_registro) VALUES (1, 50.00, CURDATE()), (3, 10.00, CURDATE())"
    execute_query(conn, query_esp)

    # Inserir Produtos
    vendedor_ids = [1, 2, 3]
    produtos_data = []
    for i in range(1, 4):
        nome = f"Produto {i}"
        valor = round(random.uniform(50.00, 500.00), 2)
        estoque = random.randint(100, 200)
        id_vendedor = random.choice(vendedor_ids)
        produtos_data.append((nome, f"Descrição {i}", estoque, valor, id_vendedor))
    
    query_produto = "INSERT INTO produto (nome, descricao, quantidade_estoque, valor, id_vendedor) VALUES (%s, %s, %s, %s, %s)"
    cursor = conn.cursor()
    cursor.executemany(query_produto, produtos_data)
    conn.commit()
    cursor.close()

    # Inserir Transportadoras
    query_transp = "INSERT INTO transportadora (nome, cidade) VALUES ('Rapidex', 'São Paulo'), ('Entrega Já', 'Rio de Janeiro')"
    execute_query(conn, query_transp)
    
    print("[SUCESSO] Dados nativos inseridos com sucesso!")

def criar_e_destruir_db():
    """ADMIN: Tenta preencher o banco de dados com dados nativos, assumindo que o DDL já foi criado."""
    if not check_permission(['Administrador']): return
    
    print("\n--- ATENÇÃO: Esta opção tentará preencher dados nativos.")
    confirm = input("Deseja tentar preencher dados nativos no DB 'ecommerce' existente? (s/n): ").lower()
    if confirm != 's':
        print("Ação cancelada.")
        return

    conn = get_db_connection()
    if not conn: 
        print("Falha na conexão. Certifique-se de que o DB 'ecommerce' existe.")
        return

    try:
        # Limpar tabelas principais antes de preencher
        execute_query(conn, "SET FOREIGN_KEY_CHECKS = 0")
        execute_query(conn, "TRUNCATE TABLE venda_produto")
        execute_query(conn, "TRUNCATE TABLE venda")
        execute_query(conn, "TRUNCATE TABLE cliente_especial")
        execute_query(conn, "TRUNCATE TABLE cliente")
        execute_query(conn, "TRUNCATE TABLE produto")
        execute_query(conn, "TRUNCATE TABLE vendedor")
        execute_query(conn, "TRUNCATE TABLE transportadora")
        execute_query(conn, "SET FOREIGN_KEY_CHECKS = 1")

        preencher_dados_nativos(conn)
        
    except Exception as e:
        print(f"[ERRO] Erro geral durante a tentativa de preenchimento: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()

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

def consultar_registros(conn):
    """GERENTE: Busca Produtos, Clientes ou Vendedores."""
    if not check_permission(['Gerente', 'Administrador']): return
    
    print("\n--- Buscar Registros (GERENTE) ---")
    print("1. Buscar Produtos | 2. Buscar Clientes | 3. Buscar Vendedores")
    escolha = input("Selecione a tabela (1/2/3): ").strip()
    
    if escolha not in ['1', '2', '3']:
        print("[ERRO] Opção inválida.")
        return

    tabela = ['produto', 'cliente', 'vendedor'][int(escolha) - 1]
    campo = input(f"Digite o nome ou parte do {tabela}: ")
    
    query = f"SELECT * FROM {tabela} WHERE nome LIKE %s LIMIT 10"
    resultados = execute_query(conn, query, (f'%{campo}%',), fetch=True)
    
    if resultados:
        print(f"\nResultados encontrados na tabela {tabela.upper()}:")
        for r in resultados:
            print(r)
    else:
        print(f"Nenhum registro encontrado em {tabela}.")
        
def editar_registro(conn):
    """GERENTE: Edição de Registros (Clientes, Produtos, Vendedores, C. Especial)."""
    if not check_permission(['Gerente', 'Administrador']): return
    
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

    campo = input("Digite o NOME do campo a ser alterado: ").strip().lower()
    novo_valor = input(f"Digite o novo valor para '{campo}': ").strip()

    try:
        if campo in ['valor', 'salario', 'cashback', 'nota_media']:
            novo_valor = float(novo_valor)
        elif campo in ['quantidade_estoque', 'idade']:
            novo_valor = int(novo_valor)
    except ValueError:
        pass 

    try:
        if campo == 'cashback' and tabela == 'cliente':
             query = f"UPDATE cliente_especial SET cashback = %s WHERE id_cliente = %s"
        elif campo == 'tipo' and tabela == 'vendedor':
             if novo_valor not in ['vendedor', 'gerente', 'CEO']:
                 print("[ERRO] Tipo de vendedor inválido (vendedor, gerente, CEO).")
                 return
             query = f"UPDATE {tabela} SET {campo} = %s WHERE id = %s"
        else:
            query = f"UPDATE {tabela} SET {campo} = %s WHERE id = %s"

        if execute_query(conn, query, (novo_valor, registro_id)):
            print(f"[SUCESSO] Registro de {tabela} ID {registro_id} atualizado com sucesso!")
        else:
            print(f"[ERRO] Falha ao editar o registro. Verifique o campo, o ID e o tipo de valor.")
    except Exception as e:
        print(f"[ERRO] Erro ao processar a edição: {e}")

def apagar_registro(conn):
    """GERENTE: Apagar Registros (Clientes, Produtos, Vendedores)."""
    if not check_permission(['Gerente', 'Administrador']): return

    print("\n--- Apagar Registros (GERENTE) ---")
    print("1. Apagar Produto | 2. Apagar Cliente | 3. Apagar Vendedor")
    escolha = input("Selecione a tabela (1/2/3): ").strip()

    if escolha not in ['1', '2', '3']:
        print("[ERRO] Opção inválida.")
        return

    tabela = ['produto', 'cliente', 'vendedor'][int(escolha) - 1]
    
    try:
        registro_id = int(input(f"Digite o ID do {tabela} a ser APAGADO: "))
    except ValueError:
        print("[ERRO] ID inválido.")
        return

    confirm = input(f"ATENÇÃO: Confirma a exclusão de {tabela} ID {registro_id}? (s/n): ").lower()
    if confirm != 's':
        print("Exclusão cancelada.")
        return

    query = f"DELETE FROM {tabela} WHERE id = %s"
    
    if execute_query(conn, query, (registro_id,)):
        print(f"[SUCESSO] {tabela.capitalize()} ID {registro_id} APAGADO com sucesso!")
    else:
        print(f"[ERRO] Falha ao apagar o registro. Pode haver vendas ou outros dados associados (chave estrangeira).")
        
def executar_reajuste(conn):
    """ADMIN: Executa Stored Procedure Reajuste."""
    if not check_permission(['Administrador']): return
    
    print("\n--- Executar Reajuste Salarial (SP Reajuste) ---")
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
    if not check_permission(['Administrador']): return

    print("\n--- Executar Sorteio de Cliente (SP Sorteio) ---")
    query = "CALL Sorteio()"
    resultados = execute_query(conn, query, fetch=True)

    if resultados:
        sorteado = resultados[0]
        print("\nO cliente sorteado é:")
        print(f"  ID: {sorteado['cliente_sorteado_id']}")
        print(f"  Nome: {sorteado['nome_sorteado']}")
        print(f"  Valor do Voucher: R$ {sorteado['valor_voucher']:.2f}")
    else:
        print("[ERRO] Falha ao executar Sorteio. Verifique se o SP existe.")

def executar_estatisticas(conn):
    """GERENTE: Executa Stored Procedure Estatísticas."""
    if not check_permission(['Gerente', 'Administrador']): return

    print("\n--- Executar Estatísticas de Vendas (SP Estatísticas) ---")
    query = "CALL Estatisticas()"
    resultados = execute_query(conn, query, fetch=True)

    if resultados:
        print("\nResultados das Estatísticas:")
        print("Produto | Total Vendido | Valor Ganho | Vendedor")
        print("-" * 60)
        for r in resultados:
            # Assumimos que o SP retorna as colunas principais
            print(f"{r['produto']:<10} | {r['total_vendido']:<13} | R$ {r['valor_ganho']:<10.2f} | {r['vendedor']}")
    else:
        print("[ERRO] Nenhum dado estatístico disponível. Verifique se o SP Estatisticas existe e se há vendas.")

# --- 7. Menus de Navegação ---

def menu_admin(conn):
    """Menu para o Administrador (Todas as permissões)."""
    while True:
        clear_screen()
        print(f"--- MENU ADMINISTRADOR (Usuário: {CURRENT_USER}) ---")
        print("1. Criar/Preencher Dados Nativos")
        print("2. Cadastrar Novo Produto/Cliente (Adição - CRUD)")
        print("--- PROCEDURES DE GESTÃO ---")
        print("3. Executar Reajuste Salarial")
        print("4. Executar Sorteio de Cliente")
        print("--- ACESSAR OUTROS MENUS ---")
        print("5. Abrir Menu do Gerente")
        print("6. Abrir Menu do Funcionário")
        print("0. Sair e Fazer Logout")
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == '1':
            criar_e_destruir_db()
            input("Pressione Enter para continuar...")
        elif choice == '2':
            print("\n1. Cadastrar Produto | 2. Cadastrar Cliente")
            sub_choice = input("Opção: ").strip()
            if sub_choice == '1': cadastrar_produto(conn)
            elif sub_choice == '2': cadastrar_cliente(conn)
            input("Pressione Enter para continuar...")
        elif choice == '3':
            executar_reajuste(conn)
            input("Pressione Enter para continuar...")
        elif choice == '4':
            executar_sorteio(conn)
            input("Pressione Enter para continuar...")
        elif choice == '5':
            menu_gerente(conn)
        elif choice == '6':
            menu_funcionario(conn)
        elif choice == '0':
            break
        else:
            print("[ERRO] Opção inválida.")
            time.sleep(1)

def menu_gerente(conn):
    """Menu para o Gerente (Busca, Edição, Apagar, Estatísticas)."""
    if not check_permission(['Gerente', 'Administrador']): return
    while True:
        clear_screen()
        print(f"--- MENU GERENTE (Usuário: {CURRENT_USER}) ---")
        print("--- CRUD ---")
        print("1. Buscar Registros (Clientes/Produtos/Vendedores)")
        print("2. Editar Registro (Cliente/Produto/Vendedor)")
        print("3. Apagar Registro (Cliente/Produto/Vendedor)")
        print("--- CONSULTA ---")
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