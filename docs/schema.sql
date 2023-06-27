CREATE TABLE router_stat (
	id INTEGER NOT NULL AUTO_INCREMENT,
	ip VARCHAR(15),
	mac CHAR(17),
	network ENUM('2.4G','5G','Ethernet','Unknown'),
	device VARCHAR(255),
	rx_rate INTEGER,
	tx_rate INTEGER,
	timestamp DATETIME,
	PRIMARY KEY (id),
	KEY ix_router_stat_ip (ip),
	KEY ix_router_stat_timestamp (timestamp)
);
