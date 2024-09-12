//
//  DayAheadWidgetView.swift
//  DayAheadWidgetView
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import Foundation
import SwiftUI
import UIKit
import WidgetKit

struct DayAheadEntry: TimelineEntry {
  let date: Date
  let intensity: Int?
  let zone: String?

  static var placeholder: DayAheadEntry {
    DayAheadEntry(

      date: Date(),
      intensity: 123,
      zone: nil
    )
  }
}

struct DayAheadWidgetView: View {
  let entry: DayAheadEntry

  var body: some View {

    if entry.zone != nil {
      VStack(alignment: .center) {

        VStack {
          Spacer()
        //   HStack {
        //     Text(String(entry.intensity ?? 0))
        //       .font(.largeTitle)
        //       .fontWeight(.heavy)
        //       .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
        //     Text("g")
        //       .font(.system(.title))
        //       .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
        //   }
        //   .padding(.top)

          Text("day ahead")
            .font(.footnote)
            
            .opacity(0.75)

          Spacer()
        }
        // HStack {
        //   Text("\(formatDate(entry.date)) · \(entry.zone ?? "?")")
        //     .font(.caption)
        //     .foregroundColor(Color(red: 0, green: 0, blue: 0, opacity: 0.4))
        //     .padding(.bottom, 5.0)
        // }
          // TODO: Widget deep link to specific zone?
          // This depends on some changes to the app in an open PR, so let's park it for now.
        //.widgetURL(URL(string: "com.tmrow.electricitymap://zone/DE"))

      }

      .frame(maxWidth: .infinity, maxHeight: .infinity)
    } else {
      VStack(alignment: .center) {
        Text("day ahead")
        Text("Open widget settings")
          .font(.body)
          .multilineTextAlignment(.center)

      }
    }

  }
  func formatDate(_ date: Date) -> String {
    let dateFormatter = DateFormatter()
    dateFormatter.dateFormat = "h:mm a"
    return dateFormatter.string(from: date)
  }

}

struct DayAheadView_Previews: PreviewProvider {
  static var previews: some View {
    Group {
        DayAheadWidgetView(
        entry: DayAheadEntry(
          date: Date(),
          intensity: 300,
          zone: "DK-DK2")
      )
      .previewContext(WidgetPreviewContext(family: .systemSmall))
    }
  }
}
