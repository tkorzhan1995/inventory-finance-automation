"""
WMS to ERP Inventory Reconciliation Module

This module compares inventory data between Warehouse Management System (WMS)
and Enterprise Resource Planning (ERP) systems to identify discrepancies.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
from loguru import logger


class WMSERPReconciliation:
    """
    Reconciles inventory data between WMS and ERP systems.
    """
    
    def __init__(self, wms_client, erp_client, tolerance: float = 0.01):
        """
        Initialize reconciliation with system clients.
        
        Args:
            wms_client: WMS API client
            erp_client: ERP API client
            tolerance: Acceptable variance threshold (default 1%)
        """
        self.wms_client = wms_client
        self.erp_client = erp_client
        self.tolerance = tolerance
        self.reconciliation_date = datetime.now()
        
    def fetch_wms_inventory(self) -> pd.DataFrame:
        """
        Fetch current inventory from WMS.
        
        Returns:
            DataFrame with columns: sku, location, quantity, last_updated
        """
        logger.info("Fetching inventory data from WMS")
        try:
            wms_data = self.wms_client.get_inventory()
            df = pd.DataFrame(wms_data)
            logger.info(f"Retrieved {len(df)} records from WMS")
            return df
        except Exception as e:
            logger.error(f"Error fetching WMS data: {e}")
            raise
            
    def fetch_erp_inventory(self) -> pd.DataFrame:
        """
        Fetch current inventory from ERP.
        
        Returns:
            DataFrame with columns: sku, location, quantity, last_updated
        """
        logger.info("Fetching inventory data from ERP")
        try:
            erp_data = self.erp_client.get_inventory()
            df = pd.DataFrame(erp_data)
            logger.info(f"Retrieved {len(df)} records from ERP")
            return df
        except Exception as e:
            logger.error(f"Error fetching ERP data: {e}")
            raise
            
    def reconcile(self) -> pd.DataFrame:
        """
        Perform reconciliation between WMS and ERP inventory.
        
        Returns:
            DataFrame with discrepancies
        """
        logger.info("Starting inventory reconciliation")
        
        # Fetch data from both systems
        wms_df = self.fetch_wms_inventory()
        erp_df = self.fetch_erp_inventory()
        
        # Merge datasets
        merged = pd.merge(
            wms_df,
            erp_df,
            on=['sku', 'location'],
            how='outer',
            suffixes=('_wms', '_erp')
        )
        
        # Fill NaN with 0 for missing records
        merged['quantity_wms'] = merged['quantity_wms'].fillna(0)
        merged['quantity_erp'] = merged['quantity_erp'].fillna(0)
        
        # Calculate variance
        merged['variance'] = merged['quantity_wms'] - merged['quantity_erp']
        merged['variance_pct'] = (
            merged['variance'] / merged['quantity_erp'].replace(0, 1) * 100
        )
        
        # Flag discrepancies outside tolerance
        merged['is_discrepancy'] = (
            abs(merged['variance_pct']) > (self.tolerance * 100)
        )
        
        # Filter to discrepancies only
        discrepancies = merged[merged['is_discrepancy']].copy()
        
        logger.info(f"Found {len(discrepancies)} discrepancies")
        
        return discrepancies
        
    def categorize_discrepancies(
        self, discrepancies: pd.DataFrame
    ) -> Dict[str, pd.DataFrame]:
        """
        Categorize discrepancies by severity and type.
        
        Args:
            discrepancies: DataFrame of discrepancies
            
        Returns:
            Dictionary with categorized discrepancies
        """
        categories = {
            'critical': discrepancies[abs(discrepancies['variance']) > 100],
            'high': discrepancies[
                (abs(discrepancies['variance']) > 50) & 
                (abs(discrepancies['variance']) <= 100)
            ],
            'medium': discrepancies[
                (abs(discrepancies['variance']) > 10) & 
                (abs(discrepancies['variance']) <= 50)
            ],
            'low': discrepancies[abs(discrepancies['variance']) <= 10],
            'negative_stock': discrepancies[
                (discrepancies['quantity_wms'] < 0) | 
                (discrepancies['quantity_erp'] < 0)
            ],
            'missing_in_wms': discrepancies[discrepancies['quantity_wms'] == 0],
            'missing_in_erp': discrepancies[discrepancies['quantity_erp'] == 0],
        }
        
        for category, df in categories.items():
            logger.info(f"{category}: {len(df)} items")
            
        return categories
        
    def generate_reconciliation_report(
        self, discrepancies: pd.DataFrame, output_path: str = None
    ) -> str:
        """
        Generate a detailed reconciliation report.
        
        Args:
            discrepancies: DataFrame of discrepancies
            output_path: Optional path to save report
            
        Returns:
            Path to generated report
        """
        if output_path is None:
            output_path = f"reports/reconciliation_{self.reconciliation_date.strftime('%Y%m%d')}.xlsx"
            
        logger.info(f"Generating reconciliation report: {output_path}")
        
        categorized = self.categorize_discrepancies(discrepancies)
        
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Summary sheet
            summary = pd.DataFrame({
                'Category': list(categorized.keys()),
                'Count': [len(df) for df in categorized.values()],
                'Total Variance': [df['variance'].sum() for df in categorized.values()]
            })
            summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # All discrepancies
            discrepancies.to_excel(writer, sheet_name='All Discrepancies', index=False)
            
            # Individual category sheets
            for category, df in categorized.items():
                if len(df) > 0:
                    df.to_excel(writer, sheet_name=category.title(), index=False)
                    
        logger.info(f"Report generated successfully: {output_path}")
        return output_path
        
    def auto_adjust_discrepancies(
        self, discrepancies: pd.DataFrame, threshold: float = 10
    ) -> List[Dict]:
        """
        Automatically adjust minor discrepancies in ERP.
        
        Args:
            discrepancies: DataFrame of discrepancies
            threshold: Maximum variance to auto-adjust
            
        Returns:
            List of adjustments made
        """
        logger.warning("Auto-adjustment is a sensitive operation")
        
        # Filter to small discrepancies only
        adjustable = discrepancies[abs(discrepancies['variance']) <= threshold]
        
        adjustments = []
        for _, row in adjustable.iterrows():
            try:
                adjustment = {
                    'sku': row['sku'],
                    'location': row['location'],
                    'old_quantity': row['quantity_erp'],
                    'new_quantity': row['quantity_wms'],
                    'adjusted_at': datetime.now()
                }
                
                # Make adjustment in ERP
                self.erp_client.adjust_inventory(
                    sku=row['sku'],
                    location=row['location'],
                    new_quantity=row['quantity_wms']
                )
                
                adjustments.append(adjustment)
                logger.info(f"Adjusted {row['sku']} at {row['location']}")
                
            except Exception as e:
                logger.error(f"Failed to adjust {row['sku']}: {e}")
                
        logger.info(f"Auto-adjusted {len(adjustments)} items")
        return adjustments