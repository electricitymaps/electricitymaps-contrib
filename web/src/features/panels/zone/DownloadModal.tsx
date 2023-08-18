import Modal from 'components/Modal';
import { isDownloadModalOpenAtom } from 'features/modals/modalAtoms';
import { useAtom } from 'jotai';
import { useState, type ReactElement } from 'react';
import { useParams } from 'react-router-dom';
import { HiArrowDownTray } from 'react-icons/hi2';

interface DownloadModalProperties {
  zoneName: string;
}

export default function DownloadModal({
  zoneName,
}: DownloadModalProperties): ReactElement {
  const [isOpen, setIsOpen] = useAtom(isDownloadModalOpenAtom);
  const { zoneId } = useParams();
  const [selectedYear, setSelectedYear] = useState('2022');
  const [selectedFrequency, setSelectedFrequency] = useState('hourly');

  return (
    <Modal isOpen={isOpen} setIsOpen={setIsOpen} title="Download Data">
      <div className="mb-4">Download CSV for: {zoneName}</div>
      <div className="mb-4">
        <select
          value={selectedYear}
          onChange={(event) => setSelectedYear(event.target.value)}
          className="w-full rounded border p-2"
        >
          <option value="2021">2021</option>
          <option value="2022">2022</option>
        </select>
      </div>
      <div className="mb-4">
        <select
          value={selectedFrequency}
          onChange={(event) => setSelectedFrequency(event.target.value)}
          className="w-full rounded border p-2"
        >
          <option value="hourly">Hourly</option>
          <option value="daily">Daily</option>
          <option value="monthly">Monthly</option>
          <option value="yearly">Yearly</option>
        </select>
      </div>
      <a
        href={`https://data.electricitymaps.com/${zoneId}_${selectedYear}_${selectedFrequency}.csv`}
        onClick={() => setIsOpen(false)}
      >
        <div>
          <button className="flex w-full items-center justify-center rounded bg-brand-green p-2 text-white hover:bg-green-800">
            <HiArrowDownTray className="mr-2" />
            Download
          </button>
        </div>
      </a>
    </Modal>
  );
}
