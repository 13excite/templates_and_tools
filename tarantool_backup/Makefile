export GOPATH=$(shell pwd)/gobuild
all:
	install -d build/usr/local/bin/ build/etc/ build/etc/systemd/system/
	install -d gobuild/src/ gobuild/pkg/
	cp -rp api_mysql_status gobuild/src/backup_api

	/usr/bin/go get -u github.com/BurntSushi/toml
	/usr/bin/go get -u github.com/go-sql-driver/mysql
	/usr/bin/go get -u github.com/gorilla/handlers
	/usr/bin/go get -u github.com/gorilla/mux


	/usr/bin/go build backup_api
	mv backup_api build/usr/local/bin/
	cp api_mysql_status/config.toml build/etc/backup_api.toml.example
	cp api_mysql_status/systemd/unit.service  build/etc/systemd/system/backup_api.service
clean:
	rm -rf build gobuild

