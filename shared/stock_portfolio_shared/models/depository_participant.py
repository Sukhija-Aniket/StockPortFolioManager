from enum import Enum

class DepositoryParticipant(Enum):
    ZERODHA = "zerodha"
    GROW = "grow"
    ICICI = "icici"
    HDFC = "hdfc"
    KOTAK = "kotak"
    ANGEL_ONE = "angel_one"
    UPSTOX = "upstox"
    FIVE_PAISA = "five_paisa"
    SHAREKHAN = "sharekhan"
    MOTILAL_OSWAL = "motilal_oswal"
    EDELWEISS = "edelweiss"
    AXIS = "axis"
    SBICAP = "sbicap"
    INDIA_INFORMS = "india_informs"
    RKSV = "rksv"
    SAMCO = "samco"
    ALICE_BLUE = "alice_blue"
    FINVASIA = "finvasia"
    MASTER_TRUST = "master_trust"
    IIFL = "iifl"
    RELIGARE = "religare"
    KARVY = "karvy"
    GEODISHA = "geodisha"
    BONANZA = "bonanza"
    ADITYA_BIRLA = "aditya_birla"
    JM_FINANCIAL = "jm_financial"
    PHILLIP_CAPITAL = "phillip_capital"
    NIRMAL_BANG = "nirmal_bang"
    PRABHUDAS_LILLADHER = "prabhudas_lilladher"
    SMC = "smc"
    YES_SECURITIES = "yes_securities"
    FIRST_GLOBAL = "first_global"
    EMKAY = "emkay"
    CENTRUM = "centrum"
    ELITE = "elite"
    LKP = "lkp"
    MIRAE_ASSET = "mirae_asset"
    NOMURA = "nomura"
    UBS = "ubs"
    CREDIT_SUISSE = "credit_suisse"
    GOLDMAN_SACHS = "goldman_sachs"
    MORGAN_STANLEY = "morgan_stanley"
    CITIGROUP = "citigroup"
    BANK_OF_AMERICA = "bank_of_america"
    JP_MORGAN = "jp_morgan"
    DEUTSCHE_BANK = "deutsche_bank"
    BARCLAYS = "barclays"
    HSBC = "hsbc"
    STANDARD_CHARTERED = "standard_chartered"
    RBL = "rbl"
    IDFC = "idfc"
    EQUIRUS = "equirus"
    ANAND_RATHI = "anand_rathi"
    SPA_SECURITIES = "spa_securities"
    VENTURA = "ventura"
    CAPITAL_VIA = "capital_via"
    TATA_CAPITAL = "tata_capital"
    BAJAJ_CAPITAL = "bajaj_capital"
    DHANUKA = "dhanuka"
    GEPL = "gepl"
    INVENTURE = "inventure"
    KRISHNA_CAPITAL = "krishna_capital"
    LKP_SECURITIES = "lkp_securities"
    MANGAL_KESHAV = "mangal_keshav"
    MARWADI = "marwadi"
    NETWORTH = "networth"
    ORIENTAL = "oriental"
    PINC = "pinc"
    PRIME = "prime"
    RATNAKAR = "ratnakar"
    SBI_CAPITAL = "sbi_capital"
    SEBI_REGISTERED = "sebi_registered"
    TAMILNADU = "tamilnadu"
    UNICON = "unicon"
    VENTURA_SECURITIES = "ventura_securities"
    WAY2WEALTH = "way2wealth"
    WEALTH_DESK = "wealth_desk"
    ZERODHA_BROKING = "zerodha_broking"
    
    @classmethod
    def get_default(cls) -> 'DepositoryParticipant':
        """Get default depository participant"""
        return cls.ZERODHA
    
    @classmethod
    def from_string(cls, value: str) -> 'DepositoryParticipant':
        """Create enum from string value, case-insensitive"""
        if not value:
            return cls.get_default()
        
        # Try exact match first
        try:
            return cls(value.lower())
        except ValueError:
            pass
        
        # Try case-insensitive match
        for participant in cls:
            if participant.value.lower() == value.lower():
                return participant
        
        # Return default if no match found
        raise ValueError(f"Invalid depository participant: {value}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"DepositoryParticipant.{self.name}" 