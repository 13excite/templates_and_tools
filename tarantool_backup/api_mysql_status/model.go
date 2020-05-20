package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
)

type backup struct {
	ID       int            `json:"backup_id"`
	Host     string         `json:"host"`
	Date     string         `json:"date"`
	Filename string         `json:"filename"`
	Status   string         `json:"status"`
	Thinning sql.NullString `json:"thinning"`
}

func (b *backup) createStatus(db *sql.DB) error {
	ctx := context.Background()
	err := db.PingContext(ctx)
	if err != nil {
		log.Fatal(err)
	}
	statement := fmt.Sprintf(
		"INSERT INTO backup(host, date, status, filename) VALUES('%s', '%s', '%s', '%s')",
		b.Host, b.Date, b.Status, b.Filename)

	_, err = db.ExecContext(ctx, statement)
	//fmt.Println(statement)
	if err != nil {
		return err
	}
	err = db.QueryRow("SELECT LAST_INSERT_ID()").Scan(&b.ID)
	if err != nil {
		return err
	}
	return nil
}

func (b *backup) selectForCheckStatus(db *sql.DB) ([]backup, error) {
	ctx := context.Background()
	err := db.PingContext(ctx)
	if err != nil {
		log.Fatal(err)
	}

	checkQuery := `SELECT host, date, status FROM backup WHERE status != 'DONE';`
	//row := db.QueryRow(checkQuery)
	rows, err := db.QueryContext(ctx, checkQuery)
	if err != nil {
		fmt.Println(err)
	}
	defer rows.Close()

	statusArr := make([]backup, 0)
	for rows.Next() {
		err := rows.Scan(&b.Host, &b.Date, &b.Status)
		if err != nil {
			return nil, err
		}
		statusArr = append(statusArr, *b)
	}

	return statusArr, nil
}

func (b *backup) getThinning(db *sql.DB) ([]backup, error) {
	ctx := context.Background()
	err := db.PingContext(ctx)
	if err != nil {
		fmt.Println(err)
	}
	thinningQuery := `SELECT backup_id, host, date, filename FROM backup  WHERE STR_TO_DATE(date, '%Y-%m-%d %H-%i-%S') < CURDATE()-INTERVAL 7 DAY  AND TIME(STR_TO_DATE(date, '%Y-%m-%d %H-%i-%S')) <= '19:00:00' and thinning is NULL`
	rows, err := db.QueryContext(ctx, thinningQuery)
	if err != nil {
		fmt.Println(err)
	}
	defer rows.Close()

	thinningArr := make([]backup, 0)
	for rows.Next() {
		err := rows.Scan(&b.ID, &b.Host, &b.Date, &b.Filename)
		if err != nil {
			return nil, err
		}
		thinningArr = append(thinningArr, *b)
	}
	return thinningArr, nil
}

func (b *backup) updateThinningStatus(db *sql.DB, backupID int) error {
	ctx := context.Background()
	err := db.PingContext(ctx)
	if err != nil {
		fmt.Println(err)
	}

	statement := fmt.Sprintf(
		"UPDATE backup set thinning='done' WHERE backup_id=%d",
		backupID)
	_, err = db.ExecContext(ctx, statement)
	//fmt.Println(statement)

	if err != nil {
		return err
	}
	return nil
}
