//
//  CO2IntensityView.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//

import Foundation
import SwiftUI
import UIKit
import WidgetKit

struct ViewSizeEntry: TimelineEntry {
  let date: Date
  let intensity: Int?
  let zone: String?

  static var placeholder: ViewSizeEntry {
    ViewSizeEntry(

      date: Date(),
      intensity: 123,
      zone: nil
    )
  }
}

struct CO2IntensityWidgetView: View {
  let entry: ViewSizeEntry

  var body: some View {

    if entry.zone != nil {
      VStack(alignment: .center) {

        VStack {
          Spacer()
          HStack {
            Text(String(entry.intensity ?? 0))
              .font(.largeTitle)
              .fontWeight(.heavy)
              .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
            Text("g")
              .font(.system(.title))
              .foregroundColor(getTextColor(intensity: entry.intensity, type: "main"))
          }
          .padding(.top)

          Text("CO₂eq/kWh")
            .font(.footnote)
            .foregroundColor(getTextColor(intensity: entry.intensity, type: "subtitle"))
            .opacity(0.75)

          Spacer()
        }
        HStack {
          Text("\(formatDate(entry.date)) · \(entry.zone ?? "?")")
            .font(.caption)
            .foregroundColor(Color(red: 0, green: 0, blue: 0, opacity: 0.4))
            .padding(.bottom, 5.0)
        }
          // TODO: Widget deep link to specific zone?
          // This depends on some changes to the app in an open PR, so let's park it for now.
        //.widgetURL(URL(string: "com.tmrow.electricitymap://zone/DE"))

      }

      .frame(maxWidth: .infinity, maxHeight: .infinity)
      // Custom function that allows us to support both ios17 and older
      .backgroundColor(for: entry)
    } else {
      VStack(alignment: .center) {
        Text("⚡️")
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
}

struct View_Previews: PreviewProvider {
  static var previews: some View {
    Group {
        CO2IntensityWidgetView(
        entry: ViewSizeEntry(
          date: Date(),
          intensity: 300,
          zone: "DK-DK2")
      )
      .previewContext(WidgetPreviewContext(family: .systemSmall))
    }
  }
}
