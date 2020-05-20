package main

import (
	"flag"
)

var config = Config{}

func init() {
	//getting config file from argument
	var configPath string
	flag.StringVar(&configPath, "c", DefaultConfigPath, "usage -c config.toml")
	flag.Parse()

	config.Read(configPath)
}


func main() {
	a := App{}
	a.Initialize(config.DB.Username, config.DB.Password, config.DB.IP, config.DB.Name, config.DB.Port)

	a.Run(config.Listen)
}
