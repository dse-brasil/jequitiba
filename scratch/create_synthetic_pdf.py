import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

def create_contract_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'ContractSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        spaceBefore=15,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'ContractBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )

    story = []
    
    # --- PAGE 1 ---
    story.append(Paragraph("CONTRATO DE PRESTAÇÃO DE SERVIÇOS DE TECNOLOGIA DA INFORMAÇÃO", title_style))
    story.append(Spacer(1, 15))
    
    intro_text = (
        "Pelo presente instrumento particular, de um lado, <b>JEQUITIBÁ LEGALTECH LTDA</b>, "
        "com sede na Av. Paulista, nº 1000, São Paulo/SP, inscrita no CNPJ/MF sob o nº 12.345.678/0001-90, "
        "doravante denominada simplesmente 'CONTRATANTE', e de outro lado, <b>USP DESENVOLVIMENTO DE SOFTWARE S/A</b>, "
        "com sede na Av. Trabalhador São-Carlense, nº 400, São Carlos/SP, inscrita no CNPJ/MF sob o nº 98.765.432/0001-10, "
        "doravante denominada simplesmente 'CONTRATADA', têm entre si justo e acordado o presente contrato, "
        "mediante as cláusulas e condições seguintes:"
    )
    story.append(Paragraph(intro_text, body_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("CLÁUSULA PRIMEIRA – DO OBJETO", section_style))
    obj_text = (
        "1.1. O presente contrato tem por objeto a prestação, pela CONTRATADA à CONTRATANTE, de serviços de "
        "desenvolvimento de software jurídico sob medida, inteligência artificial integrada, manutenção de banco de "
        "dados e suporte técnico especializado na plataforma Legal RAG."
    )
    story.append(Paragraph(obj_text, body_style))
    
    story.append(Paragraph("CLÁUSULA SEGUNDA – DAS OBRIGAÇÕES DA CONTRATANTE", section_style))
    contratante_text = (
        "2.1. A CONTRATANTE obriga-se a fornecer à CONTRATADA todas as informações, documentos, credenciais e acessos "
        "necessários para a fiel execução dos serviços de desenvolvimento de software aqui contratados.<br/>"
        "2.2. Efetuar o pagamento dos valores acordados nas datas especificadas na Cláusula Quarta deste instrumento."
    )
    story.append(Paragraph(contratante_text, body_style))
    
    story.append(PageBreak())  # Force to Page 2
    
    # --- PAGE 2 ---
    story.append(Paragraph("CLÁUSULA TERCEIRA – DAS OBRIGAÇÕES DA CONTRATADA", section_style))
    contratada_text = (
        "3.1. A CONTRATADA compromete-se a executar os serviços descritos no objeto com o mais alto padrão de qualidade e "
        "técnica, respeitando os prazos acordados no cronograma do projeto.<br/>"
        "3.2. Manter sigilo absoluto sobre todas as informações comerciais, estratégicas e dados jurídicos da CONTRATANTE "
        "a que tiver acesso durante a execução deste contrato."
    )
    story.append(Paragraph(contratada_text, body_style))
    
    story.append(Paragraph("CLÁUSULA QUARTA – DO PREÇO E CONDIÇÕES DE PAGAMENTO", section_style))
    preco_text = (
        "4.1. Pelos serviços contratados, a CONTRATANTE pagará à CONTRATADA a quantia total de R$ 150.000,00 (cento e cinquenta mil reais), "
        "divididos em 3 (três) parcelas mensais e consecutivas de R$ 50.000,00 (cinquenta mil reais), vencendo-se a primeira "
        "no dia 10 do mês subsequente ao início da execução dos serviços."
    )
    story.append(Paragraph(preco_text, body_style))
    
    story.append(Paragraph("CLÁUSULA QUINTA – DA RESCISÃO E MULTAS", section_style))
    rescisao_text = (
        "5.1. O presente contrato poderá ser rescindido imotivadamente por qualquer das partes mediante aviso prévio por escrito "
        "com antecedência mínima de 30 (trinta) dias.<br/>"
        "5.2. Em caso de rescisão motivada por descumprimento de qualquer cláusula contratual por uma das partes, a parte infratora "
        "sujeitar-se-á ao pagamento de multa penal equivalente a 10% (dez por cento) do valor total contratado, sem prejuízo de perdas e danos."
    )
    story.append(Paragraph(rescisao_text, body_style))
    
    story.append(PageBreak())  # Force to Page 3
    
    # --- PAGE 3 ---
    story.append(Paragraph("CLÁUSULA SEXTA – DA PROTEÇÃO DE DADOS (LGPD)", section_style))
    lgpd_text = (
        "6.1. As partes comprometem-se a cumprir integralmente todas as disposições da Lei Geral de Proteção de Dados Pessoais "
        "(Lei nº 13.709/2018 - LGPD), garantindo que todo tratamento de dados pessoais realizado no âmbito deste contrato ocorra de "
        "forma lícita e transparente.<br/>"
        "6.2. Em caso de incidentes de segurança ou vazamento de dados decorrentes de culpa exclusiva da CONTRATADA, esta responderá "
        "pelas perdas causadas e arcará com as multas administrativas aplicadas pela ANPD, limitadas ao valor equivalente a 2% (dois por cento) "
        "do faturamento anual da empresa."
    )
    story.append(Paragraph(lgpd_text, body_style))
    
    story.append(Paragraph("CLÁUSULA SÉTIMA – DO FORO", section_style))
    foro_text = (
        "7.1. Para dirimir quaisquer dúvidas ou controvérsias decorrentes do presente contrato, as partes elegem o foro da Comarca de "
        "São Paulo/SP, com exclusão de qualquer outro, por mais privilegiado que seja."
    )
    story.append(Paragraph(foro_text, body_style))
    
    story.append(Spacer(1, 40))
    story.append(Paragraph("São Paulo, 24 de junho de 2026.", body_style))
    
    doc.build(story)
    print(f"PDF sintético criado com sucesso em: {output_path}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    OUTPUT_DIR = os.path.join(BASE_DIR, "data", "raw_contracts")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pdf_path = os.path.join(OUTPUT_DIR, "contrato_prestacao_servicos.pdf")
    create_contract_pdf(pdf_path)
