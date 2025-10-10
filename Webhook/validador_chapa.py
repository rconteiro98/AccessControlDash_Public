import Levenshtein
import logging

LOG_FILE = 'app.log'
# Configurar logging
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, 
                    format="%(asctime)s [%(levelname)s] - %(message)s")

def corregir_chapa_detectada(chapa_detectada, cursor):
    try:
        # Evitar casos claramente inválidos
        if chapa_detectada in ["unknown", "######"] or chapa_detectada[-1] == "#":
            return "unknown"

        # Correcciones manuales conocidas
        correcciones_manual = {
            "1111": "BCU936",
            "111": "BCU936",
            "11111": "BCU936",
            "LA111": "BCU936",  
            "WBK7663":"WBKZ663",
            "BN5526":"BNS526",
            "BN5228":"BNS526",
            "BNJ228":"BNS526",
            "AAA8856":"AAAG856",
            "AAA0856":"AAAG856",
            "AAAQ856":"AAAG856",
            "AAAO859":"AAAG856",
            "AAA626":"AAAP626",
            "BAD492":"BAO492",
            "ISU2U":"WZAK462",
            "TSU2U":"WZAK462",
            "U7AV442":"WZAK462",
            "DSU241":"WZAK462",
            "8Z0610":"BZO602",
            "BZ0602":"BZO602",
            "BZOC02":"BZO602",
            "OBY981":"ORY984",
            "DRY08U":"ORY984",
            "HFVC71":"HFK671",
            "HFK871":"HFK671",
            "XAD101":"XAO101",
            "XA0101":"XAO101",
            "XAO10P":"XAO101",
            "XAD10P":"XAO101",
            "IAO101":"XAO101",
            "HFP940":"HEP940",
            "ENZ0003":"ENZO003",
            "HAE411":"HAF411",
            "HAE934":"HAF934",
            "LAL040":"ZAE648",
            "BXF592":"BXE592",
            "BXL592":"BXE592",
            "YRV859":"XRV859",
            "XRVR99":"XRV859",
            "XRV8595":"XRV859",
            "XRV855F":"XRV859",
            "09B616407":"BAO492",
            "FE98107":"BAO492",
            "A4LR942":"AALR492",
            "AAO0017":"AAOD017",
            "HAJC006":"AAJL868",
            "HAJL006":"AAJL868",
            "MHJC600":"AAJL868",
            "AADO220":"AADC220",
            "AAD0220":"AADC220",
            "AAD0330":"AADC220",
            "HALF350":"AACF336",
            "LTCF656":"AACF336",
            "HALFJ30":"AACF336",
            "HALF330":"AACF336",
            "HACF336":"AACF336",
            "AALF030":"AACF336",
            "WALF330":"AACF336",
            "DPD002":"ADP003",
            "BVT267":"BKT267",
            "DVT967":"BKT267",
            "AAD1677":"AADJ677",
            "AADJ627":"AADJ677",
            "BGU936":"BCU936",
            "AAP1949":"AAPI949",
            "AAN8674":"AANB074",
            "AANB674":"AANB074",
            "AAN8074":"AANB074",
            "AAOU11":"AADH411",
            "AAAU207":"AAAU707",
            "AAV0616":"AAVD616",
            "AAD616":"AAVD616",
            "AA3U288":"AAJU288",
            "9CG810":"OCG810",
            "AAC0210":"AACO210",
            "AAI0711":"AAIO711",
            "AAI8544":"AAIB544",
            "TOR0022":"TORO022",
            "TOR0023":"TORO023",
            "TOR0033":"TORO033",
            "TOR0034":"TORO034",
            "TCRUU34":"TORO034",
            "MBBF725":"WHBE726,",
            "AA01677":"AADJ677",
            "KAVV77":"AAFV477",
            "ATB061":"AYH061",
            "AAI0711":"AAIO711",
            "AAI8544":"AAIB544",
            "BUD834":"BUD934",
            "BRD694":"BPD694",
            "AAG0625":"AAGD625",
            "FKB341":"BKB341",
            "BKP341":"BKB341",
            "HKB34I":"BKB341",
            "RNB225":"BNB225",
            "AKR7IB":"AKR718",
            "AKB718":"AKR718",
            "AALH140":"AALP140",
            "AAV8967":"AAVB967",
            "AYA658":"AYA656",
            "BCT815":"BFT315",
            "DCF862":"OCF862",
            "AANBL74":"AANB074",
            "AAN074":"AANB074",
            "AAN0774":"AANB074",
            "HBNUT6":"HBN016",
            "III0U1":"HBN016",
            "AAAB561":"AAAB581",
            "AAF0173":"AAFD173",
            "AASB882":"AASB582",
            "AHN126":"AHH126",
            "AHHV26":"AHH126",
            "113":"AUF568",
            "BAG208":"BAG206",
            "DDD271":"BRP374",
            "EAD052":"FAD052",
            "AAYA79":"AAGY879",
            "RHY931":"BHY931",
            "DGZZUZ":"BGZ202",
            "DOLZUZ":"BGZ202",
            "BUL848":"BUL846",
            "BUL8288":"BUL846",
            "UU152":"AXU152",
            "FHH500":"BFH500",
            "AXU152":"AYU152",
            "AS942":"AALS942",
            "ILS942":"AALS942",
            "A4LR942":"AALR942",
            "CCX093":"CCK093",
            "TOR0018":"TORO018",
            "BJRJ5J":"BJR553",
            "QAO54G":"OAO546",
            "HOUU017":"HDU062",
            "HDU1067":"HDU062",
            "BTN318":"BTN918",
            "BIN318":"BTN918",
            "BTK918":"BTN918",
            "LAY725":"ZAP725",
            "BJ83911":"BJB390",
            "HDD1062":"HDU062",
        }

        if chapa_detectada in correcciones_manual:
            chapa_corregida = correcciones_manual[chapa_detectada]
            logging.info(f"Corrección manual aplicada: {chapa_detectada} => {chapa_corregida}")
            return chapa_corregida

        # Consulta directa a la BD
        cursor.execute("SELECT chapa, chapa_ca FROM moviles_movil")
        chapas_validas = cursor.fetchall()

        min_distance = float('inf')
        chapa_mas_cercana = None

        for chapa, trasera in chapas_validas:
            dist_1 = Levenshtein.distance(chapa_detectada, chapa) if chapa else float('inf')
            dist_2 = Levenshtein.distance(chapa_detectada, trasera) if trasera else float('inf')

            if dist_1 < min_distance:
                min_distance = dist_1
                chapa_mas_cercana = chapa

            if dist_2 < min_distance:
                min_distance = dist_2
                chapa_mas_cercana = trasera

        if min_distance <= 1:
            logging.info(f"Chapa corregida: {chapa_detectada} => {chapa_mas_cercana} (distancia: {min_distance})")
            return chapa_mas_cercana
        else:
            logging.info(f"No se encontró coincidencia aceptable para {chapa_detectada}")
            return chapa_detectada
    except Exception as e:
        logging.error(f"Error al validar la chapa '{chapa_detectada}': {str(e)}")
        return chapa_detectada
