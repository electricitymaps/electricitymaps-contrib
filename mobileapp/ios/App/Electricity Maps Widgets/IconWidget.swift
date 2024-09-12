//
//  IconWidget.swift
//  App
//
//  Created by SilkeBonnen on 12/09/2024.
//

import Foundation
import Intents
import SwiftUI
import WidgetKit

struct IconWidgetEntry: TimelineEntry {
    let date: Date
}

struct IconWidget: Widget {
    let kind: String = "IconWidget"

    var body: some WidgetConfiguration {
        if #available(iOS 16.0, *) {
            StaticConfiguration(
                kind: kind,
                provider: IconWidgetProvider()
            ) { entry in
                IconWidgetView(entry: entry)
            }
            .configurationDisplayName("Electricity Maps")
            .description("Displays an icon.")
            .supportedFamilies([.accessoryCircular])
        } else {
            StaticConfiguration(
                kind: kind,
                provider: IconWidgetProvider()
            ) { entry in
                IconWidgetView(entry: entry)
            }
            .configurationDisplayName("Electricity Maps")
            .description("Displays an icon.")
            .supportedFamilies([.systemSmall])
        }
    }
}

struct IconWidgetProvider: TimelineProvider {
    func placeholder(in context: Context) -> IconWidgetEntry {
        IconWidgetEntry(date: Date())
    }

    func getSnapshot(in context: Context, completion: @escaping (IconWidgetEntry) -> Void) {
        let entry = IconWidgetEntry(date: Date())
        completion(entry)
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<IconWidgetEntry>) -> Void) {
        let timeline = Timeline(entries: [IconWidgetEntry(date: Date())], policy: .never)
        completion(timeline)
    }
}

struct IconWidgetView: View {
    var entry: IconWidgetEntry
    
    var body: some View {
        if #available(iOS 17.0, *) {
            ZStack {
                Image("electricitymaps-icon-white") // Your icon name here
                    .resizable()
                    .scaledToFit()
                    .frame(width: 130, height: 130)
            }
            .containerBackground(for: .widget) {
                Color.black
            }
        } else {
            ZStack {
                Image("electricitymaps-icon-white")
                    .resizable()
                    .scaledToFit()
            }
            .background(Color.black)
        }
    }
}


struct IconWidget_Previews: PreviewProvider {
    static var previews: some View {
        if #available(iOS 16.0, *) {
            IconWidgetView(entry: IconWidgetEntry(date: Date()))
                .previewContext(WidgetPreviewContext(family: .accessoryCircular))
        } else {
            IconWidgetView(entry: IconWidgetEntry(date: Date()))
                .previewContext(WidgetPreviewContext(family: .systemSmall))
        }
    }
}
