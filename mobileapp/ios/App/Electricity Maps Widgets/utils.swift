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

func formatDate(_ date: Date) -> String {
  let dateFormatter = DateFormatter()
  dateFormatter.dateFormat = "h:mm a"
  return dateFormatter.string(from: date)
}

extension View {
    @ViewBuilder
    func backgroundColor(for entry: ViewSizeEntry) -> some View {
        if #available(iOS 17.0, *) {
            self.containerBackground(for: .widget) {
                Color(getBackgroundColor(intensity: entry.intensity))
            }
        } else {
            self.background(Color(getBackgroundColor(intensity: entry.intensity)))
        }
    }
    
    @ViewBuilder
    func backgroundColor() -> some View {
        if #available(iOS 17.0, *) {
            self.containerBackground(for: .widget) {
                Color.black
            }
        } else {
            self.background(Color.black)
        }
    }
}


