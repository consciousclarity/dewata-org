use std::io::{self, BufRead};

use balinese_calendar::BalineseDate;

fn main() {
    for line in io::stdin().lock().lines() {
        let value = line.expect("stdin read failed");
        if value.is_empty() {
            continue;
        }
        let mut parts = value.split('-');
        let year: i32 = parts.next().expect("year").parse().expect("invalid year");
        let month: u32 = parts.next().expect("month").parse().expect("invalid month");
        let day: u32 = parts.next().expect("day").parse().expect("invalid day");
        let result = BalineseDate::from_ymd(year, month, day).expect("date conversion failed");
        println!(
            "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
            value,
            result.pawukon_day,
            result.wuku.index(),
            result.wuku.name(),
            result.pancawara as usize,
            result.pancawara.name(),
            result.saptawara as usize,
            result.saptawara.name(),
            result.triwara.name(),
            result.sadwara.name(),
            result.wuku_day,
        );
    }
}
