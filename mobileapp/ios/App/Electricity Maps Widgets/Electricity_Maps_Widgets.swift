//
//  Electricity_Maps_Widgets.swift
//  Electricity Maps Widget
//
//  Created by Mads Nedergaard on 10/11/2023.
//
import Foundation
import Intents
import SwiftUI
import WidgetKit

// TODO: V2
// - Run for ios17 using xcode 15
// - use dropdown for picking zones

struct ViewSizeTimelineProvider: IntentTimelineProvider {
  typealias Entry = ViewSizeEntry

  //  Providing dummy data to the system to render a placeholder UI while waiting for the widget to get ready.
  func placeholder(in context: Context) -> Entry {
    // This will be masked, so actual input does not matter
    return ViewSizeEntry(date: Date(), intensity: 200, zone: "DE")
  }

  // Provides data required to render the widget in the widget gallery (size/type selection page)
  func getSnapshot(
    for configuration: CustomWidgetConfIntent, in context: Context,
    completion: @escaping (Entry) -> Void
  ) {
    let entry = ViewSizeEntry(date: Date(), intensity: 123, zone: "DK")
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
        let entry = ViewSizeEntry(date: Date(), intensity: nil, zone: nil)
        let timeline = Timeline(entries: [entry], policy: .never)
        completion(timeline)
      } else {

        do {
          let nextHourStart = getNextHourStart()

          let intensity = try await DataFetcher.fetchIntensity(zone: zone)
          let entry = ViewSizeEntry(date: Date(), intensity: intensity, zone: zone)
          let timeline = Timeline(entries: [entry], policy: .after(nextHourStart))
          completion(timeline)
        } catch {
          print("Error fetching intensity: \(error)")
          let entry = ViewSizeEntry(date: Date(), intensity: nil, zone: "?")
          let timeline = Timeline(entries: [entry], policy: .never)
          completion(timeline)
        }
      }
    }

    return
  }
}

// TODO: Change this from main to something else if we have multiple widgets
@main
struct ViewSizeWidget: Widget {
  let kind: String = "ViewSizeWidget"

  var body: some WidgetConfiguration {
    IntentConfiguration(
      kind: kind,
      intent: CustomWidgetConfIntent.self,
      provider: ViewSizeTimelineProvider()
    ) {
      entry in ViewSizeWidgetView(entry: entry)
    }
    .configurationDisplayName("Electricity Maps")
    .description("See the carbon intensity of your location")
    // TODO: Support other families for lock screen widgets when upgrading to ios 17
    .supportedFamilies([
      .systemSmall
    ])
  }
}

struct Widget_Previews: PreviewProvider {
  static var previews: some View {
    Group {
      ViewSizeWidgetView(
        entry: ViewSizeEntry(
          date: Date(),
          intensity: 300,
          zone: "DE")
      )
      .previewContext(WidgetPreviewContext(family: .systemSmall))
    }
  }
}
