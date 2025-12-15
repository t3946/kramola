import base64
import json

def decode_flask_session_base64_only(session_cookie_value):
    """
    Декодирует только base64 часть Flask сессии (без проверки подписи)
    Работает только если сессия не подписана или если вы знаете формат
    """
    try:
        # Flask сессия имеет формат: <data>.<signature>
        # Разделяем на части
        parts = session_cookie_value.split('.')
        if len(parts) < 2:
            print("Неверный формат сессии")
            return None
        
        # Первая часть - данные в base64
        data_part = parts[0]
        
        # Декодируем base64
        # Flask использует URL-safe base64, нужно добавить padding если нужно
        padding = 4 - len(data_part) % 4
        if padding != 4:
            data_part += '=' * padding
        
        decoded_bytes = base64.urlsafe_b64decode(data_part)
        
        # Декодируем JSON
        data = json.loads(decoded_bytes.decode('utf-8'))
        
        return data
    except Exception as e:
        print(f"Ошибка при декодировании: {e}")
        return None

r = decode_flask_session_base64_only(".eJydWtuOozgQ_Ree06OATUL6V3ZXEeEyHW2mMwpEO9Ko_30AA66rcfYhCMGpUxdXuWyH38mt7Przo-met_5cl315_rh-_7gNvz55_52c-7L793ytB0SbvCdF2drDqWnfqn1Vv9kms2-XorVvlT0dT6Y4HMrTJdklzeNxfyTvn8_bbZf8_HiUXXPu-rLvBsqv4cnjXjVdd_38fu6vP5rk3X7Ld8lsQ3u9NZ_l-DRZLWnqc4zmb_W9-jWo7-7PR9VAJvfkLVsQ_b0vb-cfZV99NINRWTHof3aDmp-Ppm7a6-dwe7t2o8F__bNL_rs_6tWB5O_n3pp0uubT9TJe7XQ1pxFRJe-nXdLqYNMs4HQXhlQRkEm9CQC9bXYDMqjLvr5U0KQqT2cf06CPDmwHRIoZrfFmm_10dU_2M2_GeFWRgnitAn3AiTHOVnefTVcn1ujGBESyOHaSLCZehwtwPsismjL_wsL7vTRMAXAqMh5fYTy-zIhT_QV2UiNEU-mTwaZSlEUYjamjt3pyirAMs6CBW2ti4rKMSwbbldGA-jKg7hrvjilQbqFoauKHJatSoqmhbs4GFiAx13EruCpV3tdthCJzmUYvHr4MxeFVZ6YY_J8IvGCeLRahKE22mZIuAtg6k7RRtFJruoCaGiRPkuRs_F7KWg7Leb5CI8UqF2HeCwsczre4FPCUcoTRlVmNuQQygkspD56_DpwANOoxjLkkzUuQv167GJ-KAuAMM87BczE3aggRDEy9uIkKjIKlQlAFGVcXuU_3MPl878soDM9jgSdfzWHguvDy-T5NpHnqS2ueIXC_R9E4gNByEZQQbhRcOrf-fgwZz7wA2G7xLYmaRgELbiMov_kJ7qIpt1QRsReFfR6QUvcdwRb1mc60OGOJOjA289DWW4PKBNEcsgpSxwpQvoFQEZhnKX2-ziMUaW-MIJqSUd-g9_LEzESkhgWnLrjJcYMjLsrDIiCLN7i5k5X33sKaXtzLmRkcPCZUts3nl541SJcUeY2iKcLSEItXuzqQbTBikYywg3UIya0j52WLFj5_a8A8AAHT5LZt2Qak2mSxOQ-yi9IRBbZQAjDvYYopRDpHUMV0XXLCBhV5sJ_TYM7XKL9QOnPY3vdF4SWoMLC4F5Wl2JZ5_uA7U2mTwW0Mi8OtQxR8cdUnewugaLclFREHz3tMH5MAX0qUFrAAQYTFeTAsIrjULAHiNUsAmSQH7ivqHYDgBRJnEPscZ7nw6ECWPIoFL6fg6wqkqJR3VuNlglq8BODivxQ7ALcNsxqef8BTItF2niW6OMsSFbp2pVM8_ejIifBDuw8oIwS7RfBqMVzAoBaWIV6Y6dsiWRS3b0AbQL8ri4GPaU_dcwxHcC-1YMud1ATNmmQv6GEOh-G0M8QIoWaLdmHr0o7vLiUctsDohIvWTIVQt-neQSenR_4cMjWJ1d_Uh8Ofz7CtjgwzOgdNaw2Sb9jiC3HpBMIMHCtINcFDHn3XooIF251COPtKpyghcEYYYf_T517BXkUQtINNTdLqTwXvaT6IfFQp3A0YPVQERoPklKSgDEnpckZNpOA2Qhdwiai8fK960XjrTa-Zv0t5qenLubgIW1Op3H7iFs3A67tcU73CJHVkpWY2ILzyLDxiuWyEwcMEW5aXJEZEHTiq4gsjcZkYFrT8YBYeeNDTY8grwPiAQVALHRT-tQqBDWGcD1MRl-VcBGZFlgJEcN0L8oHcFEljuHEXnKDzqRvwmJRVHhOk-U8SagYD8vWQBlyNiANW0UAXExgHmPvSWhkNbQCcbvCBxY8CweNjQKXgP865RQhGbaEcJqRiCSevuQCYGg3OUkNNOwCOYJyu6ZJ5L7BjQa8pB07BqdCCUpOOB2IFs1c0hRZn8eIokmgalsqbADJJjmYYfzmvBqC_AgOuRu7jpgjxy01kc2JKEbScPddFzC4CiHdRbqKFO5K1t3P3FDBeMsEd_9YHCALYz8pfI-X4qVWHPt1qykf14T7cGt5Pn6stH6WBT9XiPk37-gPc6qHR.aT_2kw.G-DX3MclGT6x153z4HJA2nq30WM")
print(r)