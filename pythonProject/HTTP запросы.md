## Товары (Products)
### Создание товара (Create)

```http
POST /products
Content-Type: application/json

{
  "name": "Название товара",
  "description": "Описание товара",
  "price": 1000,
  "quantity": 10
}
```
### Чтение информации о товаре (Read)

```http
Copy code
GET /products/{productId}
```
### Обновление товара (Update)

```http
Copy code
PUT /products/{productId}
Content-Type: application/json

{
  "name": "Новое название товара",
  "description": "Новое описание товара",
  "price": 1500,
  "quantity": 5
}
```

### Удаление товара (Delete)
```http
DELETE /products/{productId}
```
## Корзины (Carts)
### Создание корзины (Create)

```http
POST /carts
Content-Type: application/json

{
  "userId": "идентификатор пользователя"
}
```
### Чтение содержимого корзины (Read)

```http
GET /carts/{cartId}
```
### Добавление товара в корзину (Update)

```http
PUT /carts/{cartId}/add
Content-Type: application/json

{
  "productId": "идентификатор товара",
  "quantity": 2
}
```

### Очистка корзины (Delete)

```http
DELETE /carts/{cartId}
```
## Заказы (Orders)
### Создание заказа (Create)

```http
POST /orders
Content-Type: application/json

{
  "cartId": "идентификатор корзины",
  "address": "адрес доставки",
  "paymentMethod": "способ оплаты"
}
```
### Чтение информации о заказе (Read)

```http
GET /orders/{orderId}
```

### Обновление статуса заказа (Update)
```http
PUT /orders/{orderId}/status
Content-Type: application/json

{
  "status": "новый статус заказа",
}
```

### Удаление заказа (Delete)

```http
DELETE /orders/{orderId}
```