//
//  utils.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import SwiftUI

func getNextHourStart() -> Date {
  let currentDate = Date()

  let calendar = Calendar.current
  let components = calendar.dateComponents([.year, .month, .day, .hour], from: currentDate)

  guard let currentHourStartDate = calendar.date(from: components),
    let nextHourStartDate = calendar.date(byAdding: .hour, value: 1, to: currentHourStartDate)
  else {
    // If any errors occur, return the current date as a fallback
    return currentDate
  }

  return nextHourStartDate
}
