import { useState } from 'react';
import { Navigate, Route, Routes, useParams } from 'react-router-dom';

import ZoneDetails from './Zone/ZoneDetails';

function ValidZoneIdGuardWrapper({ children }: { children: JSX.Element }) {
  const { zoneId } = useParams();

  if (!zoneId) {
    return <Navigate to="/" replace />;
  }
  return children;
}

type CollapseButtonProps = {
  isCollapsed: boolean;
  onCollapse: () => void;
};

// TODO: Add icon, handle hover state
function CollapseButton({ isCollapsed, onCollapse }: CollapseButtonProps) {
  return (
    <button
      className={
        'absolute left-full top-2 z-10 h-12 w-6 cursor-pointer rounded-r bg-zinc-50 shadow-[6px_2px_10px_-3px_rgba(0,0,0,0.1)]'
      }
      onClick={onCollapse}
    >
      {isCollapsed ? '<' : '>'}
    </button>
  );
}

function OuterPanel({ children }: { children: React.ReactNode }) {
  const [isOpen, setOpen] = useState(false);
  const onCollapse = () => setOpen(!isOpen);

  return (
    <aside
      className={`duration-400 absolute left-0 top-0 z-20 h-full w-full bg-zinc-50 shadow-xl transition-all md:flex md:w-[calc(14vw_+_16rem)] ${
        isOpen && '-translate-x-full'
      }`}
    >
      <section className="w-full overflow-y-scroll p-2">{children}</section>
      <CollapseButton isCollapsed={isOpen} onCollapse={onCollapse} />
    </aside>
  );
}

export default function LeftPanel() {
  return (
    <OuterPanel>
      <Routes>
        <Route
          path="/"
          element={
            <p className="bg-blue-200">
              Ranking Panel Cillum aute occaecat in pariatur duis aliquip sint sunt
              excepteur Lorem. Incididunt quis id sit consequat reprehenderit officia
              adipisicing ipsum. Esse anim excepteur do laboris do. Nulla magna sit
              adipisicing incididunt proident tempor velit fugiat reprehenderit aute
              cillum est consectetur officia. Culpa aliquip esse sint laborum minim
              reprehenderit enim proident commodo duis pariatur officia ut. Laboris
              deserunt excepteur mollit elit amet quis cillum veniam ad laborum sit.
              Deserunt elit in nostrud magna ipsum nulla sunt ea ut reprehenderit velit
              consequat do. Nulla consequat elit non amet aliqua sunt aute nostrud magna
              dolor labore. Veniam eiusmod aliqua culpa id do incididunt incididunt in
              incididunt. Esse incididunt ipsum et deserunt Lorem non aute ut culpa qui
              enim sit enim esse. Quis laboris nostrud veniam duis tempor irure sint
              consequat reprehenderit excepteur ex ullamco. Do et cupidatat pariatur
              nostrud occaecat laboris laborum ex. Cillum aliqua incididunt tempor officia
              adipisicing excepteur reprehenderit magna quis cupidatat. Voluptate occaecat
              laboris ad ad ad irure quis est duis id adipisicing et laboris. Dolor non
              aliqua laborum enim cillum eu consequat est anim est magna velit voluptate.
              Sint dolor pariatur dolore ut in sint anim ipsum. Et ullamco veniam Lorem
              incididunt fugiat eiusmod aute aliqua elit. Magna Lorem eu ad do enim
              excepteur eiusmod dolor dolore adipisicing laborum ad. Duis sunt pariatur eu
              sit esse tempor pariatur consectetur anim aliqua laborum mollit culpa
              aliqua. Qui aliqua voluptate fugiat incididunt excepteur consequat ea
              adipisicing est deserunt incididunt. Cupidatat sit sint sunt voluptate
              minim. Culpa aliquip officia voluptate ad nostrud. Ut qui ipsum ipsum
              eiusmod nostrud fugiat in incididunt mollit ea. Non veniam sunt in minim ea.
              Id dolor nisi excepteur culpa pariatur cillum ullamco proident incididunt.
              Tempor irure aute deserunt nisi. Consequat aute Lorem ea et quis cupidatat
              aliqua officia laborum ad est quis ex sunt. Reprehenderit proident mollit
              aliqua ea magna elit. Officia sint consectetur duis sint non consectetur ad
              reprehenderit ullamco do enim. Nisi incididunt eiusmod enim enim est. Nisi
              non commodo qui fugiat exercitation sunt incididunt sit et. Nulla aliquip
              reprehenderit sint duis occaecat ipsum quis dolore aliqua aute ea quis Lorem
              deserunt. Pariatur ex aliquip velit dolore cillum. Commodo minim deserunt id
              deserunt anim aliquip. Sint fugiat duis laboris culpa voluptate officia sint
              pariatur consequat proident culpa. Veniam aliquip ut occaecat ad ut sint et
              fugiat aliquip sunt sit enim dolor minim. Sunt excepteur cillum ut minim in
              laboris occaecat eu voluptate sint et est. Ad anim irure dolore et
              incididunt enim ut nulla quis consequat culpa esse cillum in. Magna amet
              occaecat aute sunt adipisicing mollit sunt velit aliqua duis magna ad. Irure
              velit proident velit excepteur et elit officia ut consequat ut. Cupidatat
              labore id nisi elit commodo minim ut labore Lorem cupidatat nisi amet do.
              Voluptate ipsum incididunt quis qui dolore voluptate aliqua. Ut mollit
              fugiat qui nulla nulla amet est enim et laboris enim duis esse. Qui minim
              Lorem adipisicing eu cillum. Velit laboris dolore excepteur voluptate
              deserunt excepteur do. Aliquip ipsum enim veniam deserunt veniam ut nisi
              occaecat. Cupidatat magna pariatur pariatur laborum eu elit incididunt magna
              ea cupidatat velit sit enim officia. Ex labore nulla do excepteur consequat
              duis exercitation voluptate cillum incididunt deserunt. Elit excepteur
              voluptate pariatur ut tempor id veniam commodo sint laborum deserunt est
              irure. Officia fugiat ea qui nisi. Laboris sunt in qui labore voluptate ea
              consequat aliquip sit exercitation ipsum. Quis magna cillum ex adipisicing.
              Anim eiusmod amet consectetur eiusmod do pariatur excepteur eu pariatur
              ullamco nostrud irure sit. Eiusmod pariatur labore voluptate excepteur
              commodo occaecat officia anim et magna id culpa reprehenderit.
            </p>
          }
        />
        <Route
          path="/zone/:zoneId"
          element={
            <ValidZoneIdGuardWrapper>
              <ZoneDetails />
            </ValidZoneIdGuardWrapper>
          }
        />
        <Route path="/faq" element={<p>FAQ</p>} />
        {/* Alternative: add /map here and have a NotFound component for anything else*/}
        <Route path="*" element={<p>Ranking Panel</p>} />
      </Routes>
    </OuterPanel>
  );
}
