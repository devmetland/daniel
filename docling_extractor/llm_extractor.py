"""
LLM Extractor Module for Docling Extractor
Supports vLLM and any OpenAI-compatible API endpoint
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
import httpx

logger = logging.getLogger(__name__)

class LLMExtractor:
    """
    Extract structured data from text using an LLM (vLLM or OpenAI-compatible API)
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: int = 120,
        max_retries: int = 3
    ):
        """
        Initialize LLM Extractor
        
        Args:
            base_url: Base URL of the LLM API (e.g., http://localhost:8000/v1 for vLLM)
            api_key: API key for authentication
            model: Model name to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.endpoint = f"{self.base_url}/chat/completions"
        
        logger.info(f"LLM Extractor initialized with model: {model}, endpoint: {self.endpoint}")
    
    def _create_prompt(self, raw_text: str) -> str:
        """
        Create a prompt for extracting structured data from document text
        
        Args:
            raw_text: Raw text extracted from the document
            
        Returns:
            Prompt string for the LLM
        """
        prompt = f"""You are an expert document data extraction assistant. Your task is to extract specific fields from the following document text.

Document Text:
---
{raw_text}
---

Extract the following fields and return them as a valid JSON object. If a field cannot be found, set its value to null.

Fields to extract:
- invoice_number: Nomor invoice atau nomor kwitansi
- tax_invoice_number: Nomor faktur pajak (format: seri/nomor)
- npwp: NPWP (Nomor Pokok Wajib Pajak) - 15 atau 16 digit
- date: Tanggal dokumen (format: YYYY-MM-DD)
- due_date: Tanggal jatuh tempo (jika ada, format: YYYY-MM-DD)
- vendor_name: Nama perusahaan penjual/penerbit invoice
- customer_name: Nama perusahaan pembeli/pelanggan
- amount: Jumlah dasar pengenaan pajak (sebelum PPN)
- tax_amount: Jumlah PPN (Pajak Pertambahan Nilai)
- total_amount: Total jumlah yang harus dibayar (amount + tax_amount)
- currency: Kode mata uang (default: IDR)
- email: Alamat email (jika ada)
- phone: Nomor telepon (jika ada)

Important rules:
1. Return ONLY a valid JSON object, no additional text or explanation.
2. Convert all dates to YYYY-MM-DD format.
3. Convert all monetary values to numbers (without thousand separators).
4. For Indonesian documents, recognize formats like "Rp 1.000.000,-" or "Rp 1.000.000".
5. NPWP format: XX.XXX.XXX.X-XXX.XXX or continuous digits.
6. Be careful with OCR errors and try to correct obvious mistakes.

Example output format:
{{
    "invoice_number": "058/QTO-KW/XII-2025",
    "tax_invoice_number": "04002500393508587/04002500393508587",
    "npwp": "0020521332039000",
    "date": "2025-12-01",
    "due_date": null,
    "vendor_name": "PT. QREATOR TATA OPTIMA",
    "customer_name": "PT. FAJARPUTERA DINASTI",
    "amount": 135000000.00,
    "tax_amount": 14850000.00,
    "total_amount": 149850000.00,
    "currency": "IDR",
    "email": null,
    "phone": null
}}

Now extract the data from the document text above and return only the JSON object:"""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract JSON data
        
        Args:
            response_text: Raw response text from LLM
            
        Returns:
            Dictionary with extracted data
        """
        # Try to find JSON in the response
        try:
            # First, try to parse the entire response as JSON
            return json.loads(response_text.strip())
        except json.JSONDecodeError:
            # If that fails, try to find JSON within the text
            import re
            json_pattern = r'\{[\s\S]*\}'
            match = re.search(json_pattern, response_text)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from LLM response")
                    return {}
            else:
                logger.warning("No JSON found in LLM response")
                return {}
    
    async def extract(self, raw_text: str) -> Dict[str, Any]:
        """
        Extract structured data from raw text using LLM
        
        Args:
            raw_text: Raw text extracted from the document
            
        Returns:
            Dictionary with extracted structured data
        """
        if not raw_text or len(raw_text.strip()) < 10:
            logger.warning("Raw text is too short for LLM extraction")
            return {}
        
        prompt = self._create_prompt(raw_text)
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that extracts structured data from documents. Always respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # Low temperature for consistent extraction
            "max_tokens": 1000
        }
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        self.endpoint,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        if content:
                            extracted_data = self._parse_response(content)
                            if extracted_data:
                                logger.info(f"Successfully extracted {len(extracted_data)} fields from LLM")
                                return extracted_data
                            else:
                                logger.warning("LLM returned empty extraction result")
                                return {}
                        else:
                            logger.warning("LLM returned empty content")
                            return {}
                    else:
                        logger.error(f"LLM API error: {response.status_code} - {response.text}")
                        if attempt == self.max_retries - 1:
                            raise Exception(f"LLM API error: {response.status_code}")
                        
            except httpx.RequestError as e:
                logger.warning(f"Request error (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt == self.max_retries - 1:
                    raise Exception(f"Failed to connect to LLM after {self.max_retries} attempts: {str(e)}")
            
            # Wait before retrying
            import asyncio
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {}
    
    def extract_sync(self, raw_text: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for extract method
        
        Args:
            raw_text: Raw text extracted from the document
            
        Returns:
            Dictionary with extracted structured data
        """
        import asyncio
        return asyncio.run(self.extract(raw_text))


# Example usage
if __name__ == "__main__":
    # Example test
    sample_text = """
    FAKTUR PAJAK
    Nomor: 04002500393508587/04002500393508587
    Tanggal: 1 Desember 2025
    
    Penjual: PT. QREATOR TATA OPTIMA
    NPWP: 00.205.213.3-203.900
    
    Pembeli: PT. FAJARPUTERA DINASTI
    
    Harga: Rp 135.000.000
    PPN (11%): Rp 14.850.000
    Total: Rp 149.850.000
    """
    
    # This would require actual LLM setup
    print("LLM Extractor module loaded successfully")
    print("Use LLMExtractor class to extract data from documents")
