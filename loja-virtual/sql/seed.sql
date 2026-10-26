-- =====================================================================
-- Grupo 2 - Loja Virtual | Dados de exemplo (schema real do banco db2semestre)
-- Rode em banco com as 6 tabelas VAZIAS e as functions fn_criar_pedido /
-- fn_total_pedido ja criadas. Se rodar duas vezes, falha no e-mail duplicado.
-- Reproduz o exemplo do DER: Beatriz compra 1 Teclado (180,00) e
-- 2 Mouses (75,00) no cartao de credito em 3x -> total R$ 330,00.
-- =====================================================================

INSERT INTO cliente (nome, email) VALUES
    ('Beatriz Souza', 'beatriz@email.com'),
    ('Leonardo Lima', 'leonardo@email.com'),
    ('Carla Mendes',  'carla@email.com');

INSERT INTO endereco (cliente_id, logradouro, numero, cidade, uf, cep)
SELECT c.cliente_id, v.logradouro, v.numero, v.cidade, v.uf, v.cep
FROM (VALUES
    ('beatriz@email.com',  'Rua das Flores', '120', 'Sao Paulo',      'SP', '01310100'),
    ('leonardo@email.com', 'Av. Brasil',     '455', 'Rio de Janeiro', 'RJ', '20040020'),
    ('carla@email.com',    'Rua da Paz',     '78',  'Curitiba',       'PR', '80010000')
) AS v(email, logradouro, numero, cidade, uf, cep)
JOIN cliente c ON c.email = v.email;

INSERT INTO produto (sku, nome, preco_atual) VALUES
    ('TEC-001', 'Teclado',     180.00),
    ('MOU-001', 'Mouse',        75.00),
    ('MON-001', 'Monitor 24"', 899.90),
    ('CAB-001', 'Cabo HDMI',    29.90);

-- Pedidos criados pela function oficial (valida cliente e endereco).
DO $$
DECLARE
    v_bia BIGINT; v_leo BIGINT; v_carla BIGINT;
    p1 BIGINT; p2 BIGINT; p3 BIGINT; p4 BIGINT;
BEGIN
    SELECT cliente_id INTO v_bia   FROM cliente WHERE email = 'beatriz@email.com';
    SELECT cliente_id INTO v_leo   FROM cliente WHERE email = 'leonardo@email.com';
    SELECT cliente_id INTO v_carla FROM cliente WHERE email = 'carla@email.com';

    -- Pedido 1: Beatriz, o exemplo do DER, pago no cartao de credito em 3x
    p1 := fn_criar_pedido(v_bia, (SELECT endereco_id FROM endereco WHERE cliente_id = v_bia));
    INSERT INTO item_pedido (pedido_id, sku, quantidade, preco_unitario) VALUES
        (p1, 'TEC-001', 1, 180.00),
        (p1, 'MOU-001', 2,  75.00);
    INSERT INTO pagamento (pedido_id, forma_pagamento, parcelas, valor, situacao)
        VALUES (p1, 'CARTAO_CREDITO', 3, 330.00, 'APROVADO');
    UPDATE pedido SET status = 'PAGO' WHERE pedido_id = p1;

    -- Pedido 2: Leonardo, pago via Pix e ja entregue
    p2 := fn_criar_pedido(v_leo, (SELECT endereco_id FROM endereco WHERE cliente_id = v_leo));
    INSERT INTO item_pedido (pedido_id, sku, quantidade, preco_unitario) VALUES
        (p2, 'MON-001', 1, 899.90),
        (p2, 'CAB-001', 2,  29.90);
    INSERT INTO pagamento (pedido_id, forma_pagamento, parcelas, valor, situacao)
        VALUES (p2, 'PIX', 1, 959.70, 'APROVADO');
    UPDATE pedido SET status = 'ENTREGUE' WHERE pedido_id = p2;

    -- Pedido 3: Carla, aberto, pagamento parcial ainda pendente
    p3 := fn_criar_pedido(v_carla, (SELECT endereco_id FROM endereco WHERE cliente_id = v_carla));
    INSERT INTO item_pedido (pedido_id, sku, quantidade, preco_unitario) VALUES
        (p3, 'TEC-001', 1, 180.00);
    INSERT INTO pagamento (pedido_id, forma_pagamento, parcelas, valor, situacao)
        VALUES (p3, 'BOLETO', 1, 100.00, 'PENDENTE');

    -- Pedido 4: Beatriz, aberto e vazio (para testar adicionar item)
    p4 := fn_criar_pedido(v_bia, (SELECT endereco_id FROM endereco WHERE cliente_id = v_bia));
END $$;
