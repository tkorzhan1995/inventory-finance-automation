"""
Negative Stock Detector

This module detects and alerts on negative stock levels across
warehouse locations and SKUs.
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from loguru import logger


class NegativeStockDetector:
    """
    Detects negative stock levels and tracks potential causes.
    """
    
    def __init__(self, wms_client, erp_client, alert_client):
        """
        Initialize the negative stock detector.
        
        Args:
            wms_client: WMS API client
            erp_client: ERP API client
            alert_client: Alert service client
        """
        self.wms_client = wms_client
        self.erp_client = erp_client
        self.alert_client = alert_client
        
    def scan_for_negative_stock(self) -> pd.DataFrame:
        """
        Scan all inventory for negative stock levels.
        
        Returns:
            DataFrame of items with negative stock
        """
        logger.info("Scanning for negative stock levels")
        
        # Fetch inventory from both systems
        wms_inventory = self.wms_client.get_all_inventory()
        erp_inventory = self.erp_client.get_all_inventory()
        
        wms_df = pd.DataFrame(wms_inventory)
        erp_df = pd.DataFrame(erp_inventory)
        
        # Find negative quantities
        wms_negative = wms_df[wms_df['quantity'] < 0].copy()
        erp_negative = erp_df[erp_df['quantity'] < 0].copy()
        
        wms_negative['source'] = 'WMS'
        erp_negative['source'] = 'ERP'
        
        # Combine results
        negative_stock = pd.concat([wms_negative, erp_negative], ignore_index=True)
        
        if len(negative_stock) > 0:
            logger.warning(f"Found {len(negative_stock)} items with negative stock")
        else:
            logger.info("No negative stock detected")
            
        return negative_stock
        
    def analyze_negative_stock(self, negative_items: pd.DataFrame) -> Dict:
        """
        Analyze negative stock to identify patterns and causes.
        
        Args:
            negative_items: DataFrame of negative stock items
            
        Returns:
            Analysis results
        """
        logger.info("Analyzing negative stock patterns")
        
        analysis = {
            'total_items': len(negative_items),
            'by_location': negative_items.groupby('location').size().to_dict(),
            'by_category': {},
            'severity': {},
            'potential_causes': []
        }
        
        # Categorize by severity
        analysis['severity'] = {
            'minor': len(negative_items[negative_items['quantity'] > -10]),
            'moderate': len(negative_items[
                (negative_items['quantity'] <= -10) & 
                (negative_items['quantity'] > -50)
            ]),
            'severe': len(negative_items[negative_items['quantity'] <= -50])
        }
        
        # Identify potential causes
        for _, item in negative_items.iterrows():
            causes = self.identify_causes(item)
            analysis['potential_causes'].append({
                'sku': item['sku'],
                'location': item['location'],
                'quantity': item['quantity'],
                'causes': causes
            })
            
        return analysis
        
    def identify_causes(self, item: pd.Series) -> List[str]:
        """
        Identify potential causes of negative stock.
        
        Args:
            item: Negative stock item
            
        Returns:
            List of potential causes
        """
        causes = []
        
        try:
            # Check transaction history
            history = self.erp_client.get_transaction_history(
                sku=item['sku'],
                location=item['location'],
                days=7
            )
            
            # Check for over-shipment
            shipments = [t for t in history if t['type'] == 'shipment']
            if shipments:
                total_shipped = sum(t['quantity'] for t in shipments)
                if total_shipped > 0:
                    causes.append("Over-shipment detected")
                    
            # Check for missing receipts
            receipts = [t for t in history if t['type'] == 'receipt']
            if not receipts:
                causes.append("No receipts in past 7 days")
                
            # Check for adjustment errors
            adjustments = [t for t in history if t['type'] == 'adjustment']
            negative_adjustments = [a for a in adjustments if a['quantity'] < 0]
            if negative_adjustments:
                causes.append("Recent negative adjustments")
                
            # Check for timing issues
            pending_receipts = self.wms_client.get_pending_receipts(
                sku=item['sku'],
                location=item['location']
            )
            if pending_receipts:
                causes.append("Pending receipts not yet processed")
                
        except Exception as e:
            logger.error(f"Error identifying causes for {item['sku']}: {e}")
            causes.append("Unable to determine cause")
            
        return causes if causes else ["Unknown cause"]
        
    def create_remediation_plan(self, analysis: Dict) -> List[Dict]:
        """
        Create remediation actions for negative stock items.
        
        Args:
            analysis: Analysis results
            
        Returns:
            List of remediation actions
        """
        logger.info("Creating remediation plan")
        
        actions = []
        
        for item_analysis in analysis['potential_causes']:
            sku = item_analysis['sku']
            location = item_analysis['location']
            causes = item_analysis['causes']
            
            # Determine appropriate action
            if "Over-shipment detected" in causes:
                actions.append({
                    'sku': sku,
                    'location': location,
                    'action': 'investigate_shipments',
                    'priority': 'high',
                    'description': 'Review recent shipments for errors'
                })
                
            if "No receipts in past 7 days" in causes:
                actions.append({
                    'sku': sku,
                    'location': location,
                    'action': 'check_purchase_orders',
                    'priority': 'high',
                    'description': 'Verify pending purchase orders'
                })
                
            if "Pending receipts not yet processed" in causes:
                actions.append({
                    'sku': sku,
                    'location': location,
                    'action': 'process_pending_receipts',
                    'priority': 'critical',
                    'description': 'Expedite pending receipt processing'
                })
                
            # Default action for unidentified causes
            if "Unknown cause" in causes:
                actions.append({
                    'sku': sku,
                    'location': location,
                    'action': 'manual_investigation',
                    'priority': 'high',
                    'description': 'Manual review required'
                })
                
        return actions
        
    def send_alerts(self, negative_items: pd.DataFrame, analysis: Dict):
        """
        Send alerts for negative stock detection.
        
        Args:
            negative_items: DataFrame of negative stock items
            analysis: Analysis results
        """
        if len(negative_items) == 0:
            return
            
        logger.info("Sending negative stock alerts")
        
        # Create alert message
        message = f"""
        🚨 NEGATIVE STOCK ALERT 🚨
        
        Detected {analysis['total_items']} items with negative stock:
        
        Severity Breakdown:
        - Minor (< -10): {analysis['severity']['minor']}
        - Moderate (-10 to -50): {analysis['severity']['moderate']}
        - Severe (< -50): {analysis['severity']['severe']}
        
        Top Affected Locations:
        """
        
        for location, count in sorted(
            analysis['by_location'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]:
            message += f"\n  - {location}: {count} items"
            
        # Send alert
        try:
            self.alert_client.send_alert(
                subject="Negative Stock Detected",
                message=message,
                severity="high",
                attachments=[self.generate_report(negative_items)]
            )
            logger.info("Alert sent successfully")
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            
    def generate_report(self, negative_items: pd.DataFrame) -> str:
        """
        Generate detailed report of negative stock.
        
        Args:
            negative_items: DataFrame of negative stock items
            
        Returns:
            Path to report file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = f"reports/negative_stock_{timestamp}.xlsx"
        
        with pd.ExcelWriter(report_path, engine='xlsxwriter') as writer:
            negative_items.to_excel(
                writer, 
                sheet_name='Negative Stock', 
                index=False
            )
            
        logger.info(f"Report generated: {report_path}")
        return report_path
        
    def run_detection(self):
        """
        Run complete negative stock detection workflow.
        """
        logger.info("Starting negative stock detection")
        
        # Scan for negative stock
        negative_items = self.scan_for_negative_stock()
        
        if len(negative_items) > 0:
            # Analyze patterns
            analysis = self.analyze_negative_stock(negative_items)
            
            # Create remediation plan
            actions = self.create_remediation_plan(analysis)
            
            # Send alerts
            self.send_alerts(negative_items, analysis)
            
            logger.info(f"Detection complete. {len(actions)} remediation actions created")
        else:
            logger.info("No negative stock detected. All clear!")
            
        return negative_items