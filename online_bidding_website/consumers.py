# consumers.py

from channels.generic.websocket import AsyncWebsocketConsumer
import json
import openai
import mysql.connector

# 假设您已经设置了数据库配置
DB_CONFIG = {
    'host': "34.127.78.101",
    'user': "cai",
    'password': "",
    'database': "project-group1-db"
}

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        user_input = text_data_json['message']

        # 构建自定义 prompt
        db_info = """Given the following SQL tables, your job is to Write a SQL query to {user_input}. Only provide the SQL statement."
        CREATE TABLE `auctionHouse_auction` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `description` longtext NOT NULL,
  `status` varchar(30) NOT NULL,
  `start_date` date NOT NULL,
  `end_time` datetime(6) NOT NULL,
  `reserve_price` decimal(8,2) NOT NULL,
  `highest_bid` decimal(8,2) DEFAULT NULL,
  `seller_id` int NOT NULL,
  `winner_id` int DEFAULT NULL,
  `image` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_auction_seller_id_e59777ce_fk_auth_user_id` (`seller_id`),
  KEY `auctionHouse_auction_winner_id_3e3ea4d8_fk_auth_user_id` (`winner_id`),
  CONSTRAINT `auctionHouse_auction_seller_id_e59777ce_fk_auth_user_id` FOREIGN KEY (`seller_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_auction_winner_id_3e3ea4d8_fk_auth_user_id` FOREIGN KEY (`winner_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_auction_categories` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `auction_id` bigint NOT NULL,
  `category_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auctionHouse_auction_cat_auction_id_category_id_1c850366_uniq` (`auction_id`,`category_id`),
  KEY `auctionHouse_auction_category_id_7a34a45f_fk_auctionHo` (`category_id`),
  CONSTRAINT `auctionHouse_auction_auction_id_120a0acb_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_auction_category_id_7a34a45f_fk_auctionHo` FOREIGN KEY (`category_id`) REFERENCES `auctionHouse_category` (`id`)
) 
CREATE TABLE `auctionHouse_bid` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `amount` decimal(8,2) NOT NULL,
  `time` datetime(6) NOT NULL,
  `auction_id` bigint NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_bid_auction_id_5597d5c0_fk_auctionHouse_auction_id` (`auction_id`),
  KEY `auctionHouse_bid_user_id_a356cd21_fk_auth_user_id` (`user_id`),
  CONSTRAINT `auctionHouse_bid_auction_id_5597d5c0_fk_auctionHouse_auction_id` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_bid_user_id_a356cd21_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_category` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3
CREATE TABLE `auctionHouse_message` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `content` longtext NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `auction_id` bigint NOT NULL,
  `receiver_id` int NOT NULL,
  `sender_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_message_auction_id_de20b437_fk_auctionHo` (`auction_id`),
  KEY `auctionHouse_message_receiver_id_b65b3522_fk_auth_user_id` (`receiver_id`),
  KEY `auctionHouse_message_sender_id_357afddd_fk_auth_user_id` (`sender_id`),
  CONSTRAINT `auctionHouse_message_auction_id_de20b437_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_message_receiver_id_b65b3522_fk_auth_user_id` FOREIGN KEY (`receiver_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_message_sender_id_357afddd_fk_auth_user_id` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `auctionHouse_payment` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `method` varchar(20) NOT NULL,
  `status` varchar(10) NOT NULL,
  `auction_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_payment_auction_id_b0fe1d2d_fk_auctionHo` (`auction_id`),
  CONSTRAINT `auctionHouse_payment_auction_id_b0fe1d2d_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`)
) 
CREATE TABLE `auctionHouse_rating` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `rating` int NOT NULL,
  `comment` longtext,
  `auction_id` bigint NOT NULL,
  `rated_by_id` int NOT NULL,
  `rated_user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_rating_auction_id_6815e22b_fk_auctionHo` (`auction_id`),
  KEY `auctionHouse_rating_rated_by_id_8f6d19a6_fk_auth_user_id` (`rated_by_id`),
  KEY `auctionHouse_rating_rated_user_id_c4fc69ad_fk_auth_user_id` (`rated_user_id`),
  CONSTRAINT `auctionHouse_rating_auction_id_6815e22b_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`),
  CONSTRAINT `auctionHouse_rating_rated_by_id_8f6d19a6_fk_auth_user_id` FOREIGN KEY (`rated_by_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `auctionHouse_rating_rated_user_id_c4fc69ad_fk_auth_user_id` FOREIGN KEY (`rated_user_id`) REFERENCES `auth_user` (`id`)
)
CREATE TABLE `auctionHouse_shipping` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `shipping_status` varchar(15) NOT NULL,
  `auction_id` bigint NOT NULL,
  `ups_tracking_number` varchar(25) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auctionHouse_shippin_auction_id_4092668a_fk_auctionHo` (`auction_id`),
  CONSTRAINT `auctionHouse_shippin_auction_id_4092668a_fk_auctionHo` FOREIGN KEY (`auction_id`) REFERENCES `auctionHouse_auction` (`id`)
) 
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
)
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) 
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) 
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) 
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) 
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) 
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
)"""
        custom_prompt = f"{db_info}\n\nUser asks: {user_input}"

        # 调用 GPT-4 API
        openai.api_key = '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'
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": custom_prompt}]
        )
        gpt_reply = response.choices[0].message.content

        # 判断回复是否为 SQL 语句
        # 这里只是一个简单的示例，您可能需要更复杂的逻辑来确定
        if gpt_reply.strip().lower().startswith("select"):
            sql_query = gpt_reply.strip()
            try:
                # 连接数据库并执行 SQL 查询
                connection = mysql.connector.connect(**DB_CONFIG)
                cursor = connection.cursor()
                cursor.execute(sql_query)
                rows = cursor.fetchall()
                result = [dict(zip(cursor.column_names, row)) for row in rows]
                cursor.close()
                connection.close()

                # 发送 SQL 查询和结果回 WebSocket
                await self.send(text_data=json.dumps({
                    'sql_query': sql_query,
                    'result': result
                }))
            except Exception as e:
                # 发送错误信息
                await self.send(text_data=json.dumps({
                    'error': str(e)
                }))
        else:
            # 如果不是 SQL 语句，直接发送 GPT-4 的回复
            await self.send(text_data=json.dumps({
                'message': gpt_reply
            }))