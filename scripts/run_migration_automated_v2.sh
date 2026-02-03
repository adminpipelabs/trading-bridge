#!/usr/bin/expect -f
# Automated migration runner using Railway CLI
# This script connects to Railway PostgreSQL and runs the migration

set timeout 60

# Connect to Railway PostgreSQL
spawn railway connect postgres

expect {
    "railway=#" {
        puts "\n✅ Connected to Railway PostgreSQL"
    }
    "postgres=#" {
        puts "\n✅ Connected to Railway PostgreSQL"
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

# Set error stop and read SQL file
send "\\set ON_ERROR_STOP on\r"
expect {
    "railway=#" {}
    "postgres=#" {}
}

puts "\n📝 Running migrations..."

# Read and execute SQL file line by line
set fp [open "migrations/run_all_migrations.sql" r]
set lines [split [read $fp] "\n"]
close $fp

foreach line $lines {
    set trimmed [string trim $line]
    # Skip empty lines and comments
    if {$trimmed ne "" && ![string match "*--*" $trimmed] && ![string match "*=*" $trimmed]} {
        # Check if line ends with semicolon (complete SQL statement)
        if {[string index $trimmed end] eq ";"} {
            send "$trimmed\r"
            expect {
                "railway=#" {
                    puts "  ✓ Executed: [string range $trimmed 0 50]..."
                }
                "postgres=#" {
                    puts "  ✓ Executed: [string range $trimmed 0 50]..."
                }
                "ERROR:" {
                    puts "\n❌ Error: $trimmed"
                    expect -re ".*"
                    send "\\q\r"
                    exit 1
                }
                timeout {
                    puts "\n⚠️  Timeout on: $trimmed"
                }
            }
        } else {
            # Multi-line statement - accumulate until semicolon
            append current_statement "$trimmed "
        }
    }
}

# Verify migration
puts "\n🔍 Verifying migration..."
send "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bots' AND column_name IN ('health_status', 'health_message', 'last_trade_time', 'reported_status');\r"
expect {
    -re "\\s+(\\d+)" {
        set count $expect_out(1,string)
        if {$count >= 4} {
            puts "\n✅ Migration verified - $count health columns exist"
        } else {
            puts "\n⚠️  Warning: Expected 4+ columns, found $count"
        }
    }
    "railway=#" {}
    "postgres=#" {}
}

send "\\q\r"
expect eof
puts "\n✅ Migration completed successfully!"
