#!/usr/bin/expect -f
# Final automated migration runner - sends complete SQL statements

set timeout 120

spawn railway connect postgres

expect {
    "railway=#" {}
    "postgres=#" {}
    timeout { puts "\n❌ Connection timeout"; exit 1 }
    eof { puts "\n❌ Connection failed"; exit 1 }
}

send "\\set ON_ERROR_STOP on\r"
expect {
    "railway=#" {}
    "postgres=#" {}
}

puts "\n📝 Running migrations..."

# Read SQL file and send complete statements
set fp [open "migrations/run_all_migrations.sql" r]
set content [read $fp]
close $fp

# Split by semicolons to get complete statements
set statements [split $content ";"]
set prompt_regex "(railway|postgres)=#"

foreach stmt $statements {
    set trimmed [string trim $stmt]
    # Skip empty, comments, and verification queries
    if {$trimmed ne "" && ![string match "*--*" $trimmed] && ![string match "*SELECT*" $trimmed] && ![string match "*information_schema*" $trimmed]} {
        # Add semicolon back
        set full_stmt "$trimmed;"
        send "$full_stmt\r"
        expect {
            -re $prompt_regex {
                puts "  ✓ [string range [lindex [split $trimmed "\n"] 0] 0 60]..."
            }
            "ERROR:" {
                puts "\n❌ SQL Error occurred"
                expect -re ".*"
                send "\\q\r"
                exit 1
            }
            timeout {
                puts "  ⏳ Waiting..."
                expect -re $prompt_regex
            }
        }
    }
}

puts "\n🔍 Verifying..."
send "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'bots' AND column_name IN ('health_status', 'health_message', 'last_trade_time', 'reported_status');\r"
expect {
    -re "\\s+(\\d+)" {
        set count $expect_out(1,string)
        puts "\n✅ Found $count health columns"
    }
    -re $prompt_regex {}
}

send "\\q\r"
expect eof
puts "\n✅ Migration completed!"
