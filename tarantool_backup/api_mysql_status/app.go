package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"

	_ "github.com/go-sql-driver/mysql"
	"github.com/gorilla/mux"
	"github.com/gorilla/handlers"
)

type App struct {
	Router *mux.Router
	DB     *sql.DB
}

func (a *App) Initialize(user, password, server, dbname string, port int) {
	// "user:password@tcp(127.0.0.1:3306)/hello")
	connectionString := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s", user, password, server, port, dbname)
	//connectionString := fmt.Sprintf("server=%s;user_id=%s;password=%s;port=%d;database=%s;",
	//	server, user, password, port, dbname)

	var err error
	a.DB, err = sql.Open("mysql", connectionString)
	if err != nil {
		log.Fatal(err)
	}
	err = a.DB.Ping()
	if err != nil {
		log.Fatal(err)
	}

	a.Router = mux.NewRouter()
	a.initializeRoutes()
}

func (a *App) Run(addr string) {
	handlers := handlers.LoggingHandler(os.Stdout, a.Router)
	if err := http.ListenAndServe(addr, handlers); err != nil {
		log.Fatal(err)
	}
}

func (a *App) initializeRoutes() {
	a.Router.HandleFunc("/create", a.createBackupStatus).Methods("POST")
	a.Router.HandleFunc("/status", a.checkStatus).Methods("GET")
	a.Router.HandleFunc("/thinning", a.getThinning).Methods("GET")
	a.Router.HandleFunc("/update/{backup_id}", a.updateThinning).Methods("POST")
}

func (a *App) createBackupStatus(w http.ResponseWriter, r *http.Request) {
	var backupTable backup
	decoder := json.NewDecoder(r.Body)
	if err := decoder.Decode(&backupTable); err != nil {
		respondWithError(w, http.StatusBadRequest, "Invalid request payload")
		return
	}
	defer r.Body.Close()
	if err := backupTable.createStatus(a.DB); err != nil {
		respondWithError(w, http.StatusInternalServerError, err.Error())
		return
	}

	respondWithJSON(w, http.StatusCreated, backupTable)
}

func (a *App) checkStatus( w http.ResponseWriter, r *http.Request) {
	backupTable := backup{}

	result := make([]backup,0)
	defer r.Body.Close()

	result, err := backupTable.selectForCheckStatus(a.DB)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, err.Error())
	}
	respondWithJSON(w, http.StatusOK, result)
}

func (a *App) getThinning(w http.ResponseWriter, r *http.Request) {
	backupTable := backup{}
	result := make([]backup, 0)
	defer r.Body.Close()
	result, err := backupTable.getThinning(a.DB)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, err.Error())
	}
	respondWithJSON(w, http.StatusOK, result)
}

func (a *App) updateThinning(w http.ResponseWriter, r *http.Request)  {
	//get backup_id from url request
	vars := mux.Vars(r)
	backupId, err := strconv.Atoi(vars["backup_id"])
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, "backup_id need integer")
		return
	}

	defer r.Body.Close()

	backupTable := backup{}
	err = backupTable.updateThinningStatus(a.DB, backupId)
	if err != nil {
		respondWithError(w, http.StatusInternalServerError, err.Error())
		return
	}

	respondWithJSON(w, http.StatusOK, map[string]string{"status": "OK"})
}

func respondWithError(w http.ResponseWriter, code int, message string) {
	respondWithJSON(w, code, map[string]string{"error": message})
}

func respondWithJSON(w http.ResponseWriter, code int, payload interface{}) {
	response, _ := json.Marshal(payload)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	w.Write(response)
}
