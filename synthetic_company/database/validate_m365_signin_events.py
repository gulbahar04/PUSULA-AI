
import sqlite3

conn = sqlite3.connect("synthetic_company/database/company.db")
cursor = conn.cursor()

total = cursor.execute("""
    SELECT COUNT(*) FROM m365_signin_events
""").fetchone()[0]

invalid_accounts = cursor.execute("""
    SELECT COUNT(*)
    FROM m365_signin_events e
    LEFT JOIN m365_accounts a
      ON e.m365_account_id = a.m365_account_id
    WHERE a.m365_account_id IS NULL
       OR a.account_status != 'Active'
""").fetchone()[0]

invalid_sites = cursor.execute("""
    SELECT COUNT(*)
    FROM m365_signin_events e
    LEFT JOIN locations l ON e.site_id = l.site_id
    WHERE l.site_id IS NULL
""").fetchone()[0]

invalid_devices = cursor.execute("""
    SELECT COUNT(*)
    FROM m365_signin_events e
    LEFT JOIN computers c
      ON e.source_hostname = c.hostname
     AND e.source_ip = c.ip_address
     AND e.site_id = c.site_id
    WHERE c.computer_id IS NULL
""").fetchone()[0]

invalid_mfa = cursor.execute("""
    SELECT COUNT(*)
    FROM m365_signin_events e
    JOIN m365_accounts a
      ON e.m365_account_id = a.m365_account_id
    WHERE
        (a.mfa_enabled = 1 AND e.mfa_result = 'NotRequired')
        OR
        (a.mfa_enabled = 0 AND e.mfa_result IN ('Success', 'Failure'))
""").fetchone()[0]

invalid_status = cursor.execute("""
    SELECT COUNT(*)
    FROM m365_signin_events
    WHERE signin_status NOT IN ('Success', 'Failure')
       OR event_type NOT IN ('Interactive', 'NonInteractive')
""").fetchone()[0]

print("Toplam M365 olayı:", total)
print("Geçersiz veya aktif olmayan hesap:", invalid_accounts)
print("Geçersiz lokasyon:", invalid_sites)
print("Geçersiz cihaz eşleşmesi:", invalid_devices)
print("MFA tutarsızlığı:", invalid_mfa)
print("Geçersiz oturum durumu:", invalid_status)

if (
    total == 3000
    and invalid_accounts == 0
    and invalid_sites == 0
    and invalid_devices == 0
    and invalid_mfa == 0
    and invalid_status == 0
):
    print("\nSONUÇ: TÜM M365 KONTROLLERİ BAŞARILI.")
else:
    print("\nSONUÇ: KONTROL GEREKTİREN KAYITLAR VAR.")

conn.close()
