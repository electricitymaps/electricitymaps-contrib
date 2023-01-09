import { createGlobalStyle, css } from 'styled-components';

const FadeAnimationDefinition = css`
  .fade-enter {
    opacity: 0;
  }
  .fade-enter-active {
    opacity: 1;
  }
  .fade-exit {
    opacity: 1;
  }
  .fade-exit-active {
    opacity: 0;
  }
  /* Don't set display to 'none' to keep the same width and height */
  .fade-exit-done {
    opacity: 0;
    pointer-events: none;
    visibility: hidden;
  }
`;

export default createGlobalStyle`
  ${FadeAnimationDefinition}
`;
