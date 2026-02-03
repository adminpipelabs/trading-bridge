#!/usr/bin/expect -f
# Automated migration runner using Railway CLI
# This script connects to Railway PostgreSQL and runs the migration

set timeout 30
set sql_file "migrations/run_all_migrations.sql"

# Read SQL file
set fp [open $sql_file r]
set sql_content [read $fp]
close $fp

# Connect to Railway PostgreSQL
spawn railway connect postgres

expect {
    "railway=#" {
        # Successfully connected
        send "\\set ON_ERROR_STOP on\r"
        expect "railway=#"
    }
    "postgres=#" {
        # Successfully connected
        send "\\set ON_ERROR_STOP on\r"
        expect "postgres=#"
        
        # Send SQL commands line by line
        foreach line [split $sql_content "\n"] {
            if {[string trim $line] ne "" && ![string match "*--*" [string trim $line]]} {
                send "$line\r"
                expect {
                    "railway=#" {}
                    "postgres=#" {}
                    "ERROR:" {
                        puts "\n❌ Error occurred:"
                        expect -re ".*"
                        exit 1
                    }
                    timeout {
                        puts "\n⚠️  Timeout waiting for response"
                        exit 1
                    }
                }
            }
        }
        
        # Verify migration
        send "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bots' AND column_name IN ('health_status', 'health_message', 'last_trade_time');\r"
        expect {
            -re "\\s+(\\d+)" {
                set count $expect_out(1,string)
                if {$count >= 3} {
                    puts "\n✅ Migration verified - health columns exist"
                } else {
                    puts "\n⚠️  Warning: Expected 3+ columns, found $count"
                }
            }
        }
        
        send "\\q\r"
        expect eof
        puts "\n✅ Migration completed!"
    }
    timeout {
        puts "\n❌ Connection timeout"
        exit 1
    }
    eof {
        puts "\n❌ Connection failed"
        exit 1
    }
}
