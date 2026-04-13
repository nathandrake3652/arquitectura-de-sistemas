class DomainException(Exception):
    #Clase base para todas las excepciones
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)

class InsufficientStockException(DomainException):
    #Excepción para cuando un pedido supera el stock disponible
    def __init__(self, item_name: str, required: float, available: float):
        message = (
            f"Stock insuficiente para el ingrediente '{item_name}'."
            f"Se Requiere: {required}, Hay diponible: {available}"
        )
        self.item_name = item_name
        self.required = required
        self.available = available
        super().__init__(message)

class ResourceNotFoundException(DomainException):
    #Excepción para cuando un producto, receta o ingrediente no exista
    def __init__(self, resource_name: str, resource_id: int):
        message = (
            f"El recurso '{resource_name}' con ID {resource_id} no fue encontrado."
        )
        super().__init__(message)