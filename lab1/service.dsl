workspace {
    name "CDЫK"
    !identifiers hierarchical

    model {

        client = Person "Client"
        deliveryman = Person "Deliveryman"

        vehicle_service = softwareSystem "Vehicle Service"

        delivery = softwareSystem "Package Delivery System"{

            logistic_service = container "Logistic Service"{
                technology "FastAPI/PostgreSQL"
                -> vehicle_service "Gets information about available vehicles" "REST"
            }
                        
            payment_service = container "Payment Service"{
                technology "FastAPI/PostgreSQL/PayPal"
            }

            delivery_service = container "Delivery Service"{
                technology "FastAPI/PostgreSQL"
                -> logistic_service "Create shipping sсhedule" "REST"
                -> payment_service "Check payment""RabbitMQ"
            }

            client_service = container "Client Service"{
                technology "FastAPI/PostgreSQL"
                -> delivery_service "Create delivery request" "RabbitMQ"
                -> payment_service "Make payments" "RabbitMQ"
            }
            
            gateway = container "API Gateway"{
                technology "Nginx"
                -> client_service "Account management" "RabbitMQ"
                -> delivery_service "Distribute tasks among deliveryman" "RabbitMQ"
            }

            client_interface = container "Client Web Interface"{
                technology "React.js/FastAPI"
                -> gateway "Send client requests" "WebSockets"
            }

            deliverymen_interface = container "Employee Web Interface"{
                technology "React.js/FastAPI"
                -> gateway "Send employee request" "WebSockets"
            }
        }

        client -> delivery "Send Package"
        deliveryman -> delivery "Gets information about place to deliver"
        client -> delivery.client_interface "Sign In/Up, order delivery"
        deliveryman -> delivery.deliverymen_interface "Find out personal schedule"
    }


    views {
        themes default

        systemContext delivery "context" {
            include *
            autoLayout
        }

        container delivery "C2" {
            include *
            autoLayout
        }

        #Payment algorithm
        dynamic delivery {
            autoLayout lr
            client -> delivery.client_interface "Создать заказ на доставку"
            delivery.client_interface -> delivery.gateway "Направить запрос на клиентский сервис"
            delivery.gateway -> delivery.client_service "Внести данные о заказе в систему"
            delivery.client_service -> delivery.payment_service "Зарегистрировать оплату"
            delivery.client_service -> delivery.delivery_service "Передать информацию о заказе"
            delivery.delivery_service -> delivery.payment_service "Проверить платёж"
        }
    }