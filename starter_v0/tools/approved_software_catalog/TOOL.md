---
name: approved_software_catalog
track: bonus
kind: local_catalog
provider: json_file
requires_env: []
inputs: [software_name, category]
outputs: [query, category, total_found, items, policy_reference, trust_boundary]
side_effect: false
---
# approved_software_catalog

Tra cứu danh mục phần mềm được phê duyệt, bị cấm hoặc cần xin quyền của Northstar Labs từ cơ sở dữ liệu `helpdesk_data/software_catalog.json`.

## Inputs
- `software_name` (string): Tên phần mềm hoặc bí danh (ví dụ: `Docker`, `VSCode`, `AnyDesk`).
- `category` (string, enum: `[all, developer_tools, communication, remote_access, security_tools, browser]`): Phân loại nhóm phần mềm.

## Outputs
- `total_found` (integer): Số lượng phần mềm tìm thấy.
- `items` (array): Danh sách chi tiết gồm tên, trạng thái phê duyệt (`approved`, `prohibited`, `needs_approval`), loại bản quyền, phiên bản tối thiểu, người phê duyệt và hướng dẫn cài đặt.
- `policy_reference` (string): Mã chính sách bảo mật tham chiếu (`POL-SEC-04`).
- `trust_boundary` (string): Ranh giới tin cậy của dữ liệu chính sách nội bộ.

## Bảo mật và Ranh giới
- Hoàn toàn cục bộ, không gửi dữ liệu ra bên ngoài.
- Không có tác dụng phụ (side effect: false).
- Mọi phần mềm chưa nằm trong danh mục phải được coi là chưa được phép sử dụng.

