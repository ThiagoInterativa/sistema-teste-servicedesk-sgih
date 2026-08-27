# Exemplo de trecho para adicionar no app.py do seu sistema central (gestao-callcenter-noc)

# Defina a URL do seu segundo sistema Streamlit (Análise de Chamadas)
URL_ANALISE_CHAMADAS = "https://edabztnifaechep2reblaz.streamlit.app/"

def renderizar_card_analise_chamadas():
    """
    Renderiza um card moderno no topo do dashboard principal que,
    ao ser clicado, abre o sistema de análise detalhada de chamadas.
    """
    st.markdown("""
        <style>
        .analise-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid #334155;
            border-left: 6px solid #3b82f6;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            transition: all 0.3s ease;
        }
        .analise-card:hover {
            border-color: #3b82f6;
            box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.2);
            transform: translateY(-2px);
        }
        .analise-card-content {
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .analise-card-icon {
            font-size: 32px;
            background: rgba(59, 130, 246, 0.1);
            padding: 12px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .analise-card-title {
            font-size: 18px;
            font-weight: bold;
            color: #ffffff;
            margin: 0 0 4px 0;
        }
        .analise-card-desc {
            font-size: 14px;
            color: #94a3b8;
            margin: 0;
        }
        .analise-card-btn {
            background-color: #2563eb;
            color: white;
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: background-color 0.2s;
            white-space: nowrap;
        }
        .analise-card-btn:hover {
            background-color: #1d4ed8;
            color: white;
            text-decoration: none;
        }
        </style>
        
        <div class="analise-card">
            <div class="analise-card-content">
                <div class="analise-card-icon">📊</div>
                <div>
                    <h3 class="analise-card-title">Análise Avançada de Chamadas & CDR</h3>
                    <p class="analise-card-desc">Acesse métricas detalhadas, TMA, reincidência de clientes e histórico completo no PABX.</p>
                </div>
            </div>
            <a href="https://edabztnifaechep2reblaz.streamlit.app/" target="_blank" class="analise-card-btn">
                Abrir Sistema ↗
            </a>
        </div>
    """, unsafe_allow_html=True)

# No seu arquivo principal app.py, chame a função logo no início da área de exibição principal:
# renderizar_card_analise_chamadas()
