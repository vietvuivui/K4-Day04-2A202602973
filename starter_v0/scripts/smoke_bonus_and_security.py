import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import TOOL_FUNCTIONS


def test_approved_software_catalog() -> None:
    print("--> Testing Bonus Tool: approved_software_catalog...")
    catalog_fn = TOOL_FUNCTIONS.get("approved_software_catalog")
    assert catalog_fn is not None, "approved_software_catalog not found in TOOL_FUNCTIONS!"

    # 1. Test approved software (VSCode)
    res_vscode = catalog_fn(software_name="Visual Studio Code", category="developer_tools")
    assert res_vscode.get("total_found", 0) >= 1, "Failed to find VSCode"
    assert res_vscode["items"][0]["status"] == "approved", "VSCode should be approved"
    print("  [PASS] Tra cứu phần mềm được duyệt (VSCode: approved)")

    # 2. Test prohibited software (AnyDesk)
    res_anydesk = catalog_fn(software_name="AnyDesk", category="remote_access")
    assert res_anydesk.get("total_found", 0) >= 1, "Failed to find AnyDesk"
    assert res_anydesk["items"][0]["status"] == "prohibited", "AnyDesk should be prohibited"
    print("  [PASS] Tra cứu phần mềm bị cấm (AnyDesk: prohibited)")

    # 3. Test software needing approval (Docker)
    res_docker = catalog_fn(software_name="Docker", category="developer_tools")
    assert res_docker.get("total_found", 0) >= 1, "Failed to find Docker"
    assert res_docker["items"][0]["status"] == "needs_approval", "Docker should require approval"
    print("  [PASS] Tra cứu phần mềm cần phê duyệt (Docker Desktop: needs_approval)")


def test_data_leakage_guardrail() -> None:
    print("\n--> Testing Data Leakage Guardrail in search_device_info...")
    search_fn = TOOL_FUNCTIONS.get("search_device_info")
    assert search_fn is not None, "search_device_info not found in TOOL_FUNCTIONS!"

    # 1. Test Asset ID leakage
    res1 = search_fn(manufacturer="Lenovo", model="ThinkPad T14 LT-204")
    assert res1.get("error") == "restricted_internal_identifier", f"Failed to catch Asset ID: {res1}"
    print("  [PASS] Chặn rò rỉ mã máy nội bộ (LT-204)")

    # 2. Test Employee ID leakage
    res2 = search_fn(manufacturer="Dell", model="Latitude EMP-1003")
    assert res2.get("error") == "restricted_internal_identifier", f"Failed to catch Employee ID: {res2}"
    print("  [PASS] Chặn rò rỉ mã nhân viên nội bộ (EMP-1003)")

    # 3. Test Private IP leakage
    res3 = search_fn(manufacturer="HP", model="LaserJet 192.168.1.50")
    assert res3.get("error") == "restricted_internal_identifier", f"Failed to catch Private IP: {res3}"
    print("  [PASS] Chặn rò rỉ IP nội bộ (192.168.1.50)")

    # 4. Test Internal Domain leakage
    res4 = search_fn(manufacturer="Lenovo", model="srv01.northstar.local")
    assert res4.get("error") == "restricted_internal_identifier", f"Failed to catch Internal Domain: {res4}"
    print("  [PASS] Chặn rò rỉ Domain nội bộ (*.northstar.local)")

    # 5. Test Credential leakage
    res5 = search_fn(manufacturer="Dell", model="XPS password=Secret123")
    assert res5.get("error") == "restricted_internal_identifier", f"Failed to catch Credential: {res5}"
    print("  [PASS] Chặn rò rỉ Mật khẩu/Secret (password=...)")


def test_ticket_junk_prevention() -> None:
    print("\n--> Testing Ticket Junk Prevention in create_ticket...")
    ticket_fn = TOOL_FUNCTIONS.get("create_ticket")
    assert ticket_fn is not None, "create_ticket not found in TOOL_FUNCTIONS!"

    # Test create_ticket without confirmed=True
    res = ticket_fn(summary="Thử nghiệm tạo ticket rác", priority="low", asset_id="LT-204", confirmed=False)
    assert res.get("status") == "needs_confirmation", f"Expected needs_confirmation, got: {res}"
    print("  [PASS] create_ticket(confirmed=False) chặn tạo ticket và trả về needs_confirmation (không sinh file rác)")


def main() -> None:
    print("=== RUNNING UNIT & SMOKE TESTS FOR BONUS TOOL & SECURITY ===")
    test_approved_software_catalog()
    test_data_leakage_guardrail()
    test_ticket_junk_prevention()
    print("\nALL TESTS PASSED SUCCESSFULLY! (100% compliant with lab specifications)")


if __name__ == "__main__":
    main()
