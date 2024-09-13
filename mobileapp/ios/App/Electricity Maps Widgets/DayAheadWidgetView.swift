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
import SwiftUI
import Charts


struct DayAheadShape: Identifiable {
    var hour: Date // TODO: Rename this field to datetime instead
    var price: Double
    var currency: String?
    var id = UUID()
}

struct DayAheadEntry: TimelineEntry {
  let date: Date
  let zone: String?
  let data: [DayAheadShape]

  static var placeholder: DayAheadEntry {
    DayAheadEntry(

      date: Date(),
      zone: nil,
      data: [
        DayAheadShape(hour: Date(), price: 12.34),
        DayAheadShape(hour: Date(), price: 14.56)
      ]

    )
  }
}

struct DayAheadWidgetView: View {
    let entry: DayAheadEntry

    let percentile = 0.2; // boundary for colors, 0.2 = 20%
    // Helper to determine upper and lower bounds
    private var minPrice: Double? {
        let prices = entry.data.map { $0.price }.sorted()
        // Calculate the index for the 10th percentile
        guard !prices.isEmpty else { return nil }
        let percentileIndex = Int(Double(prices.count) * 0.2)
        return prices[min(percentileIndex, prices.count - 1)]
    }
    private var maxPrice: Double? {
        let prices = entry.data.map { $0.price }.sorted()
        // Calculate the index for the 10th percentile
        guard !prices.isEmpty else { return nil }
        let percentileIndex = Int(Double(prices.count) * 0.2)
        return prices[max(percentileIndex, prices.count - 1)]
    }


    var body: some View {
        if let minPrice = minPrice, let maxPrice = maxPrice {
            VStack(alignment: .center) {
                Chart {
                    ForEach(entry.data) { data in
                        BarMark(
                            x: .value("Hour", data.hour),
                            y: .value("Price", data.price)
                        )
                        .foregroundStyle(color(for: data.price, minPrice: minPrice, maxPrice: maxPrice))

                    }
                    .interpolationMethod(.cardinal)
                }
                .chartYAxis(.hidden)


            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .containerBackground(.white, for: .widget)
        } else {
            VStack(alignment: .center) {
                Text("day ahead")
                Text("Open widget settings")
                    .font(.body)
                    .multilineTextAlignment(.center)
            }
        }
    }


    // Function to determine color based on price
    private func color(for price: Double, minPrice: Double, maxPrice: Double) -> LinearGradient {
        if price >= maxPrice {
            return LinearGradient(
                gradient: Gradient(colors: [
                    Color.red.opacity(0.8),
                    Color.red.opacity(0.5)
                ]),
                startPoint: .top,
                endPoint: .bottom
            )
        } else if price <= minPrice {
            return LinearGradient(
                gradient: Gradient(colors: [
                    Color.green.opacity(0.8),
                    Color.green.opacity(0.5)
                ]),
                startPoint: .top,
                endPoint: .bottom
            )

        } else {
             return LinearGradient(
                gradient: Gradient(colors: [
                    Color.cyan.opacity(0.6),
                    Color.cyan.opacity(0.2)
                ]),
                startPoint: .top,
                endPoint: .bottom
            )
            // Default color for other points
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
          zone: "DK-DK2",
          data: [
            // Note that the dates provided here are UTC, so in preview they will be shifted ahead 1-2 hours
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T08:00:00Z")!, price: 12.34),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T09:00:00Z")!, price: 102.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T10:00:00Z")!, price: 12.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T11:00:00Z")!, price: 12.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T12:00:00Z")!, price: 89.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T13:00:00Z")!, price: 10.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T14:00:00Z")!, price: 53.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T15:00:00Z")!, price: 53.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T16:00:00Z")!, price: 33.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T17:00:00Z")!, price: 23.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T18:00:00Z")!, price: 13.43),
            DayAheadShape(hour: iso8601Date(from: "2024-09-12T19:00:00Z")!, price: 73.43),
          ]
        )
      )
      .previewContext(WidgetPreviewContext(family: .systemSmall))
    }
  }
}
