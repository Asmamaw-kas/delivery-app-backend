class PaymentError(Exception):
    """Base exception for payment errors"""
    pass

class ChapaAPIError(PaymentError):
    """Exception for Chapa API errors"""
    def __init__(self, message, status_code=None, response_data=None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

class PaymentVerificationError(PaymentError):
    """Exception for payment verification errors"""
    pass

class PaymentNotFoundError(PaymentError):
    """Exception when payment is not found"""
    pass

class InvalidPaymentDataError(PaymentError):
    """Exception for invalid payment data"""
    pass

class WebhookVerificationError(PaymentError):
    """Exception for webhook verification errors"""
    pass