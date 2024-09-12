//
//  RenewableWidget.swift
//  Electricity Maps Widget
//
//  Created by SilkeBonnen on 12/09/2024.
//

import Foundation
import Foundation
import Intents
import SwiftUI
import WidgetKit

struct ViewRenewableTimelineProvider: IntentTimelineProvider {
  typealias Entry = ViewRenewableEntry

  //  Providing dummy data to the system to render a placeholder UI while waiting for the widget to get ready.
  func placeholder(in context: Context) -> Entry {
    // This will be masked, so actual input does not matter
    return ViewRenewableEntry(date: Date(), renewablePercentage: 200, zone: "DE")
  }

  // Provides data required to render the widget in the widget gallery (size/type selection page)
  func getSnapshot(
    for configuration: CustomWidgetConfIntent, in context: Context,
    completion: @escaping (Entry) -> Void
  ) {
    let entry = ViewRenewableEntry(date: Date(), renewablePercentage: 123, zone: "DK")
    completion(entry)
  }

  // Provides an array of timeline entries for the current time and, optionally, any future times to update a widget
  func getTimeline(
    for configuration: CustomWidgetConfIntent,
    in context: Context, completion: @escaping (Timeline<Entry>) -> Void
  ) {
    Task {
      let zone = configuration.area ?? "?"

      if zone == "?" {
        let entry = ViewRenewableEntry(date: Date(), renewablePercentage: nil, zone: nil)
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
      } else {

        do {
          let nextHourStart = getNextHourStartt()

          let intensity = try await DataFetcherr.fetchIntensity(zone: zone)
          let entry = ViewRenewableEntry(date: Date(), renewablePercentage: intensity, zone: zone)
          let timeline = Timeline(entries: [entry], policy: .after(nextHourStart))
          completion(timeline)
        } catch {
          print("Error fetching intensity: \(error)")
          let entry = ViewRenewableEntry(date: Date(), renewablePercentage: nil, zone: "?")
          let timeline = Timeline(entries: [entry], policy: .never)
          completion(timeline)
        }
      }
    }
    return
  }
}

func getNextHourStartt() -> Date {
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

struct RenewableWidget: Widget {
  let kind: String = "RenewableWidget"

  var body: some WidgetConfiguration {
    IntentConfiguration(
      kind: kind,
      intent: CustomWidgetConfIntent.self,
      provider: ViewRenewableTimelineProvider()
    ) {
      entry in RenewableWidgetView(entry: entry)
    }
    .configurationDisplayName("Electricity Maps")
    .description("See the renewable percentage")
    // TODO: Support other families for lock screen widgets when upgrading to ios 17
    .supportedFamilies([
        .systemSmall,
    ])
  }
}

struct Widget_renewable_Previews: PreviewProvider {
  static var previews: some View {
    Group {
        RenewableWidgetView(
        entry: ViewRenewableEntry(
          date: Date(),
          renewablePercentage: 300,
          zone: "DE")
      )
      .previewContext(WidgetPreviewContext(family: .systemSmall))
    }
  }
}

struct APIResponsee: Decodable {
  let _disclaimer: String
  let status: String
  let countryCode: String
  let data: ElectricityDetailss
  let units: ElectricityUnitss
}

struct ElectricityDetailss: Codable {
  let datetime: String
  let carbonIntensity: Int
  let fossilFuelPercentage: Double
}

struct ElectricityUnitss: Codable {
  let carbonIntensity: String
}

struct DataFetcherr {
  static func fetchIntensity(zone: String) async throws -> Int {
    // TODO: Validate zone name here
    let url = URL(string: "https://api.co2signal.com/v1/latest?countryCode=\(zone)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    let result = try JSONDecoder().decode(
      APIResponsee.self, from: data)

    return Int(result.data.carbonIntensity)
  }
}
