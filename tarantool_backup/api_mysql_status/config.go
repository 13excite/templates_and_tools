package main


import (
	"github.com/BurntSushi/toml"
	"log"
)

//DefaultConfigPath is path to toml config,
//usage if have not -c --config key when run script
const DefaultConfigPath = "./config.toml"

//Config struct represents api,database server and credentials settings
type Config struct {
	Listen		string
	DB database `toml:"database"`
}

// database nested struct for base config
type database struct {
	IP string
	Port int
	Username string
	Password string
	Name	string
}

// Read and parse the configuration file
func (c *Config) Read(configPath string) {
	if configPath == "" {
		configPath = DefaultConfigPath
	}
	if _, err := toml.DecodeFile(configPath, &c); err != nil {
		log.Fatal(err)
	}
}
