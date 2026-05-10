"""Unit tests onboarding state machine + validate_cnpj edge cases (sem DB).

Cobre `bloco_auth/onboarding.py` lógica pura (sem persistence):
- State machine in-memory (_SESSIONS dict + start_session/store_step/get_session/reset_sessions)
- validate_cnpj algoritmo módulo 11 BR (edge cases)

Testes integration de complete_onboarding (triple insert atomic) ficam em
tests/integration/test_onboarding_e2e.py (chunk 7 — skip se sem DB).

Story SP04-AUTH-01 AC-08 unit coverage.
"""

from __future__ import annotations

import re
import uuid

import pytest

from bloco_auth import onboarding
from bloco_auth.onboarding import (
    OnboardingError,
    OnboardingStep1Data,
    OnboardingStep2Data,
    OnboardingStep3Data,
    OnboardingStep4Data,
    get_session,
    reset_sessions,
    start_session,
    store_step,
    validate_cnpj,
)


_UUID4_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    """Limpa _SESSIONS dict entre tests (sem leak cross-test)."""
    reset_sessions()
    yield
    reset_sessions()


def _valid_step1_data() -> OnboardingStep1Data:
    """Helper — instancia OnboardingStep1Data com dados válidos."""
    return OnboardingStep1Data(
        cnpj="11222333000181",  # CNPJ canônico válido (módulo 11)
        razao_social="Escritório de Teste Ltda",
        advogado_responsavel="João da Silva",
        email="joao@escritorio-teste.com",
        senha="senha-forte-12345",
    )


# ──────────────────────────────────────────────────────────────────────────────
# State machine tests
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_start_session_returns_uuid4() -> None:
    """start_session retorna string UUID4 válida."""
    session_id = start_session(_valid_step1_data())
    assert _UUID4_RE.match(session_id), f"Esperado UUID4 válido, recebido: {session_id}"


@pytest.mark.unit
def test_start_session_stores_step1() -> None:
    """Após start_session, get_session retorna dict com step1 preenchido."""
    sid = start_session(_valid_step1_data())
    session = get_session(sid)
    assert session["step1"] is not None
    assert session["step1"].cnpj == "11222333000181"
    assert session["step2"] is None
    assert session["step3"] is None
    assert session["step4"] is None


@pytest.mark.unit
def test_store_step_invalid_session_raises() -> None:
    """store_step com session_id inexistente → OnboardingError."""
    fake_uuid = str(uuid.uuid4())
    step2 = OnboardingStep2Data(anthropic_api_key="sk-test-1234567890")
    with pytest.raises(OnboardingError, match="Sessão.*não encontrada"):
        store_step(fake_uuid, 2, step2)


@pytest.mark.unit
def test_store_step_out_of_order_raises() -> None:
    """store_step pulando ordem (step3 sem step2) → OnboardingError."""
    sid = start_session(_valid_step1_data())
    step3 = OnboardingStep3Data(dpa_version="1.0.0", accepted=True)
    with pytest.raises(OnboardingError, match="Step 2 não completado"):
        store_step(sid, 3, step3)


@pytest.mark.unit
def test_store_step_invalid_step_n_raises() -> None:
    """store_step com step_n fora do range 2-4 → OnboardingError."""
    sid = start_session(_valid_step1_data())
    step1 = _valid_step1_data()
    with pytest.raises(OnboardingError, match="Step 1 inválido|Step.*inválido"):
        store_step(sid, 1, step1)


@pytest.mark.unit
def test_store_step_sequential_succeeds() -> None:
    """store_step em ordem (2 → 3 → 4) sucesso."""
    sid = start_session(_valid_step1_data())
    store_step(sid, 2, OnboardingStep2Data(anthropic_api_key="sk-ant-test1234567890"))
    store_step(sid, 3, OnboardingStep3Data(dpa_version="1.0.0", accepted=True))
    store_step(sid, 4, OnboardingStep4Data(tier="Starter"))

    session = get_session(sid)
    assert session["step2"].anthropic_api_key.startswith("sk-ant")
    assert session["step3"].dpa_version == "1.0.0"
    assert session["step4"].tier == "Starter"


@pytest.mark.unit
def test_get_session_invalid_raises() -> None:
    """get_session com UUID4 fake → OnboardingError."""
    fake_uuid = str(uuid.uuid4())
    with pytest.raises(OnboardingError, match="não encontrada"):
        get_session(fake_uuid)


@pytest.mark.unit
def test_reset_sessions_clears_state() -> None:
    """reset_sessions limpa todas sessões in-flight."""
    sid_a = start_session(_valid_step1_data())
    sid_b = start_session(_valid_step1_data())
    sid_c = start_session(_valid_step1_data())
    assert all(sid != "" for sid in (sid_a, sid_b, sid_c))

    reset_sessions()
    for sid in (sid_a, sid_b, sid_c):
        with pytest.raises(OnboardingError):
            get_session(sid)


# ──────────────────────────────────────────────────────────────────────────────
# validate_cnpj edge cases (algoritmo módulo 11)
# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.unit
def test_validate_cnpj_repeated_digits_rejected() -> None:
    """CNPJ com todos dígitos iguais (anti-gaming) → False."""
    for digit in "0123456789":
        cnpj = digit * 14
        assert not validate_cnpj(cnpj), f"CNPJ {cnpj} deveria ser rejeitado"


@pytest.mark.unit
def test_validate_cnpj_invalid_length_rejected() -> None:
    """CNPJ com length != 14 → False."""
    assert not validate_cnpj("123")
    assert not validate_cnpj("12345678901234567890")
    assert not validate_cnpj("")


@pytest.mark.unit
def test_validate_cnpj_non_digit_rejected() -> None:
    """CNPJ com chars não-numéricos → False."""
    assert not validate_cnpj("ABCDEFGHIJKLMN")
    assert not validate_cnpj("1122233300018X")


@pytest.mark.unit
def test_validate_cnpj_valid_real_examples() -> None:
    """CNPJs válidos conhecidos (algoritmo módulo 11) → True."""
    assert validate_cnpj("11222333000181"), "CNPJ canônico ALU teste"
    assert validate_cnpj("11444777000161"), "CNPJ canônico variante"


@pytest.mark.unit
def test_validate_cnpj_wrong_check_digit() -> None:
    """CNPJ com último dígito alterado → False."""
    # Original válido: 11222333000181 → último dígito 1
    # Alterar para qualquer outro: deve falhar
    for digit in "0234567890":  # exclui 1 (correto)
        invalid = "1122233300018" + digit
        assert not validate_cnpj(invalid), f"CNPJ {invalid} deveria ser rejeitado"


@pytest.mark.unit
def test_validate_cnpj_wrong_first_check_digit() -> None:
    """CNPJ com penúltimo dígito alterado → False."""
    # Original válido: 11222333000181 → penúltimo 8
    invalid = "11222333000171"  # penúltimo alterado para 7
    assert not validate_cnpj(invalid)
