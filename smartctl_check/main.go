package main

import (
	"fmt"
	"log"
	"os"
	"os/exec"
	"regexp"
)

// Disks describe disk name with his smart propetries
type Disks struct {
	device string
	value  *Smart
}

// Smart describe smart status disk's properties
type Smart struct {
	Capacity              string
	ReallocatedEventCount string
	CurrentPendingSector  string
	Temperature           string
	PowerOnHours          string
}
type disksCollection struct {
	Data []Disks
}

// WorkerSmart is a struct for describe running smrtctl tool
type WorkerSmart struct {
	Command string
	Args    string
	Disk    string
}

// Run method is a smartctl runner
func (cmd *WorkerSmart) Run() string {
	out, err := exec.Command(cmd.Command, cmd.Args, cmd.Disk).Output()
	if err != nil {
		log.Fatal(err)
	}
	return string(out)
}

/* func for tests, when get data from files
func getDataFromFile(filePath string) []byte {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		log.Fatal(err)
	}
	return data
}
*/
func getDisksFromSas() []byte {
	data, err := exec.Command("/bin/bash", "-c", "/bin/ls -al /sys/block/sd*/device").CombinedOutput()
	if err != nil {
		os.Stderr.WriteString(err.Error())
		os.Exit(1)
	}
	return data
}
func bytesToString(data []byte) string {
	return string(data[:])
}

func regexpParse(data string, delimetr string) string {
	re := regexp.MustCompile(delimetr)
	return re.FindStringSubmatch(data)[1]
}

func parseDisks(data string, delimetr string) [][]string {
	re := regexp.MustCompile(delimetr)
	return re.FindAllStringSubmatch(data, -1)
}

func main() {
	/*   need for tests
	filePath := flag.String("path", "", "usage -p /data/smat.out")
	flag.Parse()
	file := *filePath
	if file == "" {
		flag.Usage()
		os.Exit(1)
	}

	fmt.Println(bytesToString(getDataFromFile(file)))
	*/
	fmt.Println("TTTTTTTTTTTTT")

	disks := parseDisks(bytesToString(getDisksFromSas()), `block/(.*)/device -> ../../.*`)

	//temperature := regexpParse(bytesToString(getDataFromFile(file)), `Temperature_Celsius.*\-\s+(\d+)`)[1]
	//testSmart := Smart{Capacity: "10", ReallocatedEventCount: 20, CurrentPendingSector: 34, PowerOnHours: 2300, Temperature: temperature}

	var testDsk disksCollection
	//chanSmart := make(chan string)
	//var fullSmart string
	for _, element := range disks {
		var fullDiskPath string
		fullDiskPath = "/dev/" + element[1]

		smartCmd := &WorkerSmart{Command: "smartctl", Args: "-a", Disk: fullDiskPath}
		fullSmart := smartCmd.Run()

		temperature := regexpParse(fullSmart, `Temperature_Celsius.*\-\s+(\d+)`)
		rellocate := regexpParse(fullSmart, `Reallocated_Sector_Ct.*\-\s+(\d+)`)
		pennding := regexpParse(fullSmart, `Current_Pending_Sector.*\-\s+(\d+)`)
		workHours := regexpParse(fullSmart, `Power_On_Hours.*\-\s+(\d+)`)

		testDsk.Data = append(testDsk.Data, Disks{fullDiskPath, &Smart{Capacity: "10", ReallocatedEventCount: rellocate, CurrentPendingSector: pennding, PowerOnHours: workHours, Temperature: temperature}})
	}
	//	fmt.Println(testDsk.Data)
	for _, elm := range testDsk.Data {
		fmt.Printf("disk=%s; Capacity=%s, Relloc=%s, Pending=%s, Hours=%s  Temp=%s\n", elm.device, elm.value.Capacity, elm.value.ReallocatedEventCount, elm.value.CurrentPendingSector, elm.value.PowerOnHours, elm.value.Temperature)
	}
}
