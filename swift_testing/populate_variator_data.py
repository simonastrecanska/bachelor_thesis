#!/usr/bin/env python3
"""
Populate Variator Data

This script populates the variator_data table with sample data for the TemplateVariator.
The data will be used to add variations to SWIFT message templates, making generated
messages more diverse and realistic for testing purposes.
"""

import argparse
import logging
import yaml
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

Base = declarative_base()

class VariatorData(Base):
    """VariatorData model for the variator_data table."""
    __tablename__ = 'variator_data'
    
    id = Column(Integer, primary_key=True)
    data_type = Column(String(100), nullable=False)
    data_value = Column(String(255), nullable=False)
    
    def __repr__(self):
        return f"<VariatorData(id={self.id}, type='{self.data_type}', value='{self.data_value}')>"

def load_config(config_path):
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dict containing the configuration
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

def get_db_connection_string(config):
    """
    Extract database connection string from config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Database connection string
    """
    return config['database']['connection_string']

def create_table_if_not_exists(engine):
    """
    Create the variator_data table if it doesn't exist.
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.create_all(engine)
    logger.info("Ensured variator_data table exists")

def clear_existing_data(engine):
    """
    Clear existing data from the variator_data table.
    
    Args:
        engine: SQLAlchemy engine
    """
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM variator_data"))
        logger.info("Cleared existing data from variator_data table")

def get_data_categories():
    """Return a dictionary of data categories and their values for the variator."""
    return {
        'currencies': [
            "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "SGD", "HKD", 
            "CNY", "SEK", "NOK", "DKK", "ZAR", "MXN", "BRL", "INR", "RUB", "THB"
        ],
        'bank_prefixes': [
            "BANK", "FIN", "CITI", "TRAD", "PAY", "TRUST", "METRO", "WEST", "EAST", "UNION", 
            "ROYAL", "NATL", "FIRST", "INTER", "GLOBAL", "PACIFIC", "TRANS", "CREDIT", "CAPITAL", "PRIME",
            "ABCDE", "ALPHA", "DELTA", "SWIFT", "CHASE", "WELLS", "BARCLAYS", "DEUTSCHE", "SANTANDER", "HSBC"
        ],
        'bank_suffixes': [
            "US", "EU", "GB", "JP", "CN", "SG", "AU", "DE", "FR", "IT", 
            "ES", "CA", "CH", "KR", "HK", "BR", "MX", "IN", "AE", "SA",
            "FGH", "XYZ", "ABC", "BBB", "CCC", "DDD", "EEE", "FFF", "GGG", "HHH"
        ],
        'payment_types': [
            "INVOICE", "PAYMENT", "TRANSFER", "SALARY", "COMMISSION", "SERVICES", "CONSULTING", 
            "DIVIDEND", "ROYALTY", "LICENSING", "RENTAL", "SUBSCRIPTION", "INTEREST", "LOAN", "REFUND",
            "PAYMENT FOR INVOICE", "SERVICES PAYMENT", "CONSULTING FEE", "SALARY TRANSFER", "GOODS PAYMENT",
            "INVOICE PAYMENT", "MONTHLY INVOICE", "QUARTERLY PAYMENT", "ANNUAL SUBSCRIPTION", "MAINTENANCE FEE"
        ],
        'reference_prefixes': [
            "REF", "INV", "TR", "PAY", "PO", "TX", "SL", "FC", "TF", "PMT", 
            "CTR", "ACH", "WIR", "FX", "DIV", "AP", "AR", "STMT", "REB", "BONU",
            "CUSTREF", "INVOICE", "PAYMENT", "ORDER", "CONTRACT", "SWIFT", "TRANSFER", "BATCH", "DIRECT", "INTL"
        ],
        'first_names': [
            "JOHN", "JANE", "ROBERT", "MARY", "DAVID", "LISA", "MICHAEL", "SARAH", "JAMES", "EMILY", 
            "WILLIAM", "EMMA", "JOSEPH", "OLIVIA", "RICHARD", "SOPHIA", "THOMAS", "ISABELLA", "CHARLES", "MIA"
        ],
        'last_names': [
            "SMITH", "JONES", "BROWN", "JOHNSON", "DAVIS", "MILLER", "WILSON", "MOORE", "ANDERSON", "TAYLOR", 
            "THOMAS", "JACKSON", "WHITE", "HARRIS", "MARTIN", "THOMPSON", "GARCIA", "MARTINEZ", "ROBINSON", "CLARK"
        ],
        'street_names': [
            "MAIN", "HIGH", "PARK", "OAK", "PINE", "MAPLE", "BROADWAY", "MARKET", "RIVER", "LAKE", 
            "FOREST", "MEADOW", "SUNSET", "HILL", "VALLEY", "SPRING", "OCEAN", "MOUNTAIN", "CEDAR", "WILLOW"
        ],
        'street_types': [
            "STREET", "AVENUE", "ROAD", "BOULEVARD", "DRIVE", "LANE", "PLACE", "COURT", "WAY", "CIRCLE", 
            "TERRACE", "PATH", "TRAIL", "PLAZA", "SQUARE", "CROSSING", "GROVE", "PARK", "ALLEY", "HIGHWAY"
        ],
        'cities': [
            "NEW YORK", "LONDON", "PARIS", "BERLIN", "TOKYO", "SYDNEY", "SINGAPORE", "HONG KONG", "MADRID", "ROME", 
            "DUBAI", "TORONTO", "MOSCOW", "BEIJING", "SAO PAULO", "MUMBAI", "ISTANBUL", "SEOUL", "MEXICO CITY", "AMSTERDAM"
        ],
        'company_prefixes': [
            "GLOBAL", "UNITED", "FIRST", "INTER", "TRANS", "MEGA", "MICRO", "NEW", "EASTERN", "WESTERN", 
            "NATIONAL", "PACIFIC", "METRO", "ALPHA", "BETA", "DELTA", "SIGMA", "CENTRAL", "CROWN", "PRIME"
        ],
        'company_mids': [
            "BANK", "TRADE", "FINANCE", "TECH", "SYSTEMS", "SOLUTIONS", "PARTNERS", "HOLDINGS", "INSURANCE", "INVESTMENTS", 
            "LOGISTICS", "EXPORTS", "IMPORTS", "INDUSTRIES", "ENERGY", "HEALTHCARE", "TELECOM", "MEDIA", "DIGITAL", "ASSET"
        ],
        'company_suffixes': [
            "LTD", "INC", "CORP", "LLC", "PLC", "SA", "AG", "GROUP", "CO", "TRUST", 
            "HOLDINGS", "PARTNERS", "ASSOCIATES", "INTERNATIONAL", "WORLDWIDE", "GLOBAL", "ENTERPRISES", "VENTURES", "CAPITAL", "SERVICES"
        ],
        'mt103_references': [
            "CUSTREFNO123", "CUSTREFNO456", "CUSTREFNO789", "SWIFTREF001", "SWIFTREF002", 
            "PAYREF2023", "INVREF2023", "TRANSFER2023", "PAYMENT0001", "PAYMENT0002",
            "INVNO12345", "INVNO54321", "PAYMNT2023", "ORDER12345", "CONTRACT001"
        ],
        'account_numbers': [
            "12345678901234", "98765432109876", "11223344556677", "55667788991010", 
            "11223311223311", "99887766554433", "12121212121212", "34343434343434",
            "11111222223333", "44444555556666", "77777888889999", "10203040506070"
        ],
        'amount_values': [
            "100000,00", "250000,00", "500000,00", "750000,00", "1000000,00", 
            "1500000,00", "2000000,00", "5000000,00", "10000,00", "25000,00", 
            "50000,00", "75000,00", "125000,00", "175000,00", "225000,00"
        ],
        'invoice_numbers': [
            "12345", "54321", "98765", "56789", "13579", "24680", "11111", 
            "22222", "33333", "44444", "55555", "66666", "77777", "88888", "99999"
        ],
        'ordering_customers': [
            "ORDERING CUSTOMER NAME", "ACME CORPORATION", "GLOBAL ENTERPRISES", 
            "SMITH INDUSTRIES", "TECH SOLUTIONS INC", "FIRST FINANCIAL GROUP",
            "ADVANTAGE CONSULTING", "SUMMIT PARTNERS LLC", "UNITED EXPORTERS SA", 
            "INTERNATIONAL TRADE CO", "PRECISION MANUFACTURING"
        ],
        'beneficiary_names': [
            "BENEFICIARY NAME", "GLOBAL IMPORTS LTD", "EUROPEAN DISTRIBUTORS", 
            "ASIA PACIFIC TRADING", "CONTINENTAL SUPPLIES", "NORTHERN SERVICES INC",
            "WORLDWIDE LOGISTICS", "TRANSCONTINENTAL SHIPPING", "METRO WHOLESALERS", 
            "UNIVERSAL EXPORTS", "STANDARD MANUFACTURING"
        ],
        'payment_detail_templates': [
            "PAYMENT FOR SERVICES",
            "CONSULTING FEE",
            "PRODUCT PURCHASE",
            "COMMISSION",
            "INVOICE SETTLEMENT",
            "TRANSFER TO ACCOUNT",
            "CONTRACT PAYMENT",
            "INVOICE {number:10000:99999}",
            "PAYMENT REF: {string:8}",
            "ORDER {number:1000:9999}/{number:1:99}",
            "CONTRACT {number:100000:999999}"
        ],
        'instruction_templates': [
            "PLEASE CREDIT BENEFICIARY ACCOUNT PROMPTLY",
            "REF: {string:8}",
            "DO NOT CONVERT - KEEP IN ORIGINAL CURRENCY",
            "CHARGES TO BE PAID BY BENEFICIARY",
            "CHARGES TO BE PAID BY ORDERING CUSTOMER",
            "PAYMENT RELATED TO CONTRACT {string:6}",
            "NOTIFY BENEFICIARY UPON RECEIPT"
        ]
    }

def populate_variator_data(session):
    """
    Populate the variator_data table with sample data.
    
    Args:
        session: SQLAlchemy session
    """
    data_categories = get_data_categories()
    
    total_records = 0
    
    for data_type, values in data_categories.items():
        for value in values:
            record = VariatorData(data_type=data_type, data_value=value)
            session.add(record)
            total_records += 1
    
    session.commit()
    logger.info(f"Added {total_records} records to variator_data table across {len(data_categories)} categories")

def main():
    """Main function to populate the variator_data table."""
    parser = argparse.ArgumentParser(description='Populate variator_data table for SWIFT message variator')
    parser.add_argument('--config', required=True, help='Path to config file')
    parser.add_argument('--clear', action='store_true', help='Clear existing data before inserting new data')
    args = parser.parse_args()
    
    config = load_config(args.config)
    
    db_uri = get_db_connection_string(config)
    logger.info(f"Using database: {db_uri}")
    
    engine = create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        create_table_if_not_exists(engine)
        
        if args.clear:
            clear_existing_data(engine)
        
        populate_variator_data(session)
        
        logger.info("Successfully populated variator_data table")
    except Exception as e:
        logger.error(f"Error populating variator_data: {e}")
        raise
    finally:
        session.close()
        
if __name__ == "__main__":
    main() 