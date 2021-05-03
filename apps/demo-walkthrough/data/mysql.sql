drop database if exists demo;
create database demo;

use demo;

create table customers (
	id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
	customer_name varchar(20) NOT NULL UNIQUE,
	address varchar(100),
	longitude decimal(18,6),
	latitude decimal(18,6)
);

insert into customers (customer_name,address,longitude,latitude)
values
('Jones','1745 T Street Southeast','-76.979235','38.867033'),
('Kivell','6007 Applegate Lane','-85.6498512','38.1343013'),
('Jardine','560 Penstock Drive','-121.077583','39.213076'),
('Gill','150 Carter Street','-72.473091','41.76556'),
('Sorvino','2721 Lindsay Avenue','-85.700243','38.263793'),
('Andrews','18 Densmore Drive','-73.101883','44.492953'),
('Thompson','637 Britannia Drive','-122.193849','38.1047699999999'),
('Morgan','5601 West Crocus Drive','-112.179737','33.6152469'),
('Howard','5403 Illinois Avenue','-86.853827','36.157077'),
('Parent','8821 West Myrtle Avenue','-112.2488391','33.5404296'),
('Smith','2203 7th Street Road','-85.779006','38.218107')
;
