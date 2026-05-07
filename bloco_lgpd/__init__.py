"""bloco_lgpd — defense-in-depth LGPD camadas L3/L4/L5 (MVP-LEAN-01 Task 8).

L1+L2 já implementadas em Tasks 2 (auth bcrypt + SessionMiddleware).
L3 headers HTTP CSP — bloco_lgpd/headers.py
L4 encryption-at-rest Fernet — bloco_lgpd/encryption.py
L5 permissões filesystem — bloco_lgpd/permissions.py
"""
